"""Validate a density guess and read-only DF tensors before a fresh SCF solve.

Sampled Coulomb Gram matrices are invariant to auxiliary eigenvector signs.
This is a compatibility check, not an estimate of the physical method error.
"""
import hashlib,inspect,json
from pathlib import Path
from types import MethodType
import numpy as np


def sha(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024**2),b''):value.update(block)
    return value.hexdigest()


def basis_signature(mol):
    payload=json.dumps({'cart':mol.cart,'basis':mol._basis},sort_keys=True,
                       default=lambda x:x.tolist()).encode()
    return hashlib.sha256(payload).hexdigest()


def density_guess(mol,checkpoint):
    from pyscf import lib
    old=lib.chkfile.load_mol(str(checkpoint));scf=lib.chkfile.load(str(checkpoint),'scf')
    if (mol.natm,mol.charge,mol.spin,mol.nelectron)!=(old.natm,old.charge,old.spin,old.nelectron):
        raise ValueError('Restart molecular state changed')
    if [mol.atom_symbol(i) for i in range(mol.natm)]!=[old.atom_symbol(i) for i in range(old.natm)]:
        raise ValueError('Restart atom order changed')
    if np.max(abs(mol.atom_coords()-old.atom_coords()))>1e-9 or basis_signature(mol)!=basis_signature(old):
        raise ValueError('Restart geometry or orbital basis changed')
    C=np.asarray(scf['mo_coeff']);occ=np.asarray(scf['mo_occ'])
    if set(occ)!={0.,2.}:raise ValueError('Closed-shell density required')
    S=mol.intor_symmetric('int1e_ovlp');D=(C*occ)@C.T
    electrons=float(np.einsum('ij,ji',D,S));metric=float(np.max(abs(C.T@S@C-np.eye(C.shape[1]))))
    if abs(electrons-mol.nelectron)>1e-6 or metric>1e-7:raise ValueError('Restart density metric/count failed')
    return D,{'density_electrons':electrons,'MO_metric_max_error':metric,
              'checkpoint_sha256':sha(checkpoint),'orbital_basis_sha256':basis_signature(mol),
              'scope':'Initial density only; no previous SCF convergence or energy is accepted'}


def _cached_columns(group,indices,rank,nao_pair):
    keys=sorted(group.keys(),key=int)
    if keys!=[str(i) for i in range(len(keys))]:raise ValueError('Noncontiguous DF blocks')
    lengths=[]
    for key in keys:
        ds=group[key]
        if ds.ndim!=2 or ds.shape[0]!=rank or ds.dtype!=np.dtype('float64'):raise ValueError('DF shape/dtype changed')
        lengths.append(ds.shape[1])
    ends=np.cumsum(lengths)
    if not len(ends) or ends[-1]!=nao_pair:raise ValueError('Incomplete AO-pair coverage in cache')
    starts=np.r_[0,ends[:-1]];answer=np.empty((rank,len(indices)))
    buckets={}
    for output,index in enumerate(indices):
        block=int(np.searchsorted(ends,index,side='right'));buckets.setdefault(block,[]).append((output,int(index-starts[block])))
    for block,entries in buckets.items():
        local=sorted({j for _,j in entries});values=group[str(block)][:,local]
        offsets={j:i for i,j in enumerate(local)}
        for output,j in entries:answer[:,output]=values[:,offsets[j]]
    return answer,len(keys)


def verify_and_attach_df(mf,cache, *, gram_absolute_tolerance=1e-8,gram_relative_tolerance=1e-7):
    import h5py
    import scipy.linalg
    from pyscf import df,gto
    from pyscf.df import outcore
    mol=mf.mol;aux=df.addons.make_auxmol(mol,mf.with_df.auxbasis)
    omega,alpha,hybrid=mf._numint.rsh_and_hybrid_coeff(mf.xc,spin=mol.spin)
    orders=[(0.,'j3c')]+([(float(omega),f'j3c-lr/{omega:.6f}')] if omega else [])
    nao=mol.nao_nr();nao_pair=nao*(nao+1)//2;loc=mol.ao_loc_nr()
    shells=sorted(set([(0,0),(mol.nbas//2,mol.nbas//2),(mol.nbas-1,mol.nbas-1),
                       (mol.nbas//3,0),(mol.nbas-1,mol.nbas//2)]))
    reports=[]
    with h5py.File(cache,'r') as stored:
        for value,groupname in orders:
            if groupname not in stored:raise ValueError('Required full/range DF group missing: '+groupname)
            with mol.with_range_coulomb(value),aux.with_range_coulomb(value):
                metric=aux.intor('int2c2e',hermi=1)
                try:low=scipy.linalg.cholesky(metric,lower=True);decomposition='CD'
                except scipy.linalg.LinAlgError:low=outcore._eig_decompose(mol,metric);decomposition='ED'
                atm,bas,env=gto.mole.conc_env(mol._atm,mol._bas,mol._env,aux._atm,aux._bas,aux._env)
                intor=mol._add_suffix('int3c2e');ao_loc=gto.moleintor.make_loc(bas,intor);columns={}
                for a,b in shells:
                    raw=gto.moleintor.getints3c(intor,atm,bas,env,
                        shls_slice=(a,a+1,b,b+1,mol.nbas,mol.nbas+aux.nbas),aosym='s1',ao_loc=ao_loc)
                    ni,nj=raw.shape[:2];matrix=raw.transpose(2,0,1).reshape(aux.nao_nr(),-1)
                    rebuilt=scipy.linalg.solve_triangular(low,matrix,lower=True) if decomposition=='CD' else low@matrix
                    for i in range(ni):
                        for j in range(nj):
                            ia,ja=int(loc[a]+i),int(loc[b]+j)
                            if ia>=ja:columns[ia*(ia+1)//2+ja]=rebuilt[:,i*nj+j]
                indices=sorted(columns);direct=np.column_stack([columns[i] for i in indices])
                cached,blocks=_cached_columns(stored[groupname],indices,direct.shape[0],nao_pair)
                if not np.isfinite(cached).all():raise ValueError('Nonfinite cached integrals')
                G=direct.T@direct;H=cached.T@cached
                absolute=float(np.max(abs(G-H)));relative=float(np.linalg.norm(G-H)/max(np.linalg.norm(G),1e-30))
                if absolute>gram_absolute_tolerance or relative>gram_relative_tolerance:
                    raise ValueError(f'DF cache/direct-integral compatibility failed for {groupname}: {absolute}, {relative}')
                reports.append({'group':groupname,'omega':value,'decomposition':decomposition,'auxiliary_rank':direct.shape[0],
                    'blocks':blocks,'sampled_AO_pair_indices':indices,'max_Gram_difference':absolute,
                    'relative_Gram_difference':relative})
    # Attach only after all groups pass; PySCF opens these tensors for reading.
    mf.with_df._cderi=str(Path(cache).resolve());mf.with_df.auxmol=aux;attached=[mf.with_df]
    for value,_ in orders[1:]:
        with mf.with_df.range_coulomb(value) as ranged:
            ranged._cderi=str(Path(cache).resolve());ranged.auxmol=aux;attached.append(ranged)
    def refuse_rebuild(self,*args,**kwargs):
        raise RuntimeError('Validated read-only DF cache mode forbids rebuilding integral tensors')
    for fitting in attached:fitting.build=MethodType(refuse_rebuild,fitting)
    return {'status':'PASS','scope':'Read-only DF compatibility using recomputed sampled Coulomb Gram matrices; not full physical validation',
        'cache_sha256':sha(cache),'cache_bytes':Path(cache).stat().st_size,'orbital_basis_sha256':basis_signature(mol),
        'auxiliary_basis_sha256':basis_signature(aux),'AO_count':nao,'AO_pair_count':nao_pair,
        'rsh_coefficients':[float(omega),float(alpha),float(hybrid)],'groups':reports,
        'absolute_tolerance':gram_absolute_tolerance,'relative_tolerance':gram_relative_tolerance,
        'tensor_rebuild_allowed':False,
        'eigen_cutoff':float(outcore.LINEAR_DEP_THR),
        'metric_decomposition_source_sha256':hashlib.sha256(inspect.getsource(outcore._eig_decompose).encode()).hexdigest()}
