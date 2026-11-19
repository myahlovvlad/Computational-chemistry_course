from pathlib import Path
import json,shutil,subprocess,sys
import numpy as np
from pyscf import gto,dft,lib
from scipy.constants import physical_constants
R=Path(__file__).resolve().parents[1];out=R/'practicuum/evidence/20261119-electronic-checkpoint-controls';out.mkdir(exist_ok=False)
shutil.copyfile(__file__,out/'control-source.py');lib.num_threads(1)
fixture=out/'actual-water';fixture.mkdir()
mol=gto.M(atom='O 0 0 0; H 0 .757 .587; H 0 -.757 .587',basis='def2-svp',verbose=0,max_memory=1000)
mf=dft.RKS(mol).density_fit();mf.xc='CAM-B3LYP';mf=mf.PCM();mf.with_solvent.method='C-PCM'
mf.with_solvent.eps=78.3553;mf.with_solvent.eps_optical=1.78;mf.with_solvent.lebedev_order=17
mf.chkfile=str(fixture/'checkpoint.h5');mf.conv_tol=1e-10;mf.kernel()
td=mf.TDDFT();td.nstates=3;td.conv_tol=1e-7;td.with_solvent.equilibrium_solvation=False;e,_=td.kernel()
if not mf.converged or not np.all(td.converged):raise ValueError('Actual water control did not converge')
f=td.oscillator_strength(gauge='length');v=td.oscillator_strength(gauge='velocity');factor=physical_constants['Hartree energy in eV'][0]
(fixture/'input.xyz').write_text('3\nActual water checkpoint control, not a drug case\n'+ '\n'.join(mol.atom_symbol(i)+' '+' '.join(f'{x:.12f}' for x in mol.atom_coord(i,unit='Angstrom')) for i in range(3))+'\n')
manifest={'all_electrons':10,'protocol':{'functional':'CAM-B3LYP','static_dielectric':78.3553,'optical_dielectric':1.78},
 'scope':'Actual H2O calculation to check independent checkpoint analysis; not course target-drug evidence'}
(fixture/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(fixture/'result.json').write_text(json.dumps({'status':'PASS','transitions':[{'energy_eV':float(x*factor),'oscillator_strength_length':float(y),'oscillator_strength_velocity':float(z)} for x,y,z in zip(e,f,v)]},indent=2)+'\n')
positive=subprocess.run([sys.executable,'scripts/analyze_electronic_checkpoint.py','--run',str(fixture),'--out',str(out/'positive')],cwd=R)
if positive.returncode:raise RuntimeError('Positive checkpoint control failed')
bad=out/'deliberately-corrupted-electron-count';shutil.copytree(fixture,bad);manifest['all_electrons']=11;manifest['scope']='Deliberate negative control: mismatched count, not a physical result'
(bad/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
negative=subprocess.run([sys.executable,'scripts/analyze_electronic_checkpoint.py','--run',str(bad),'--out',str(out/'expected-rejection')],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(out/'negative-control.log').write_bytes(negative.stdout)
failure=json.loads((out/'expected-rejection/failure.json').read_text())
if negative.returncode==0 or failure['status']!='FAIL' or 'Density' not in failure['message']:raise RuntimeError('Corrupted count not rejected as expected')
(out/'summary.json').write_text(json.dumps({'status':'PASS','actual_water_calculation':'PASS','independent_density_and_TD_reconstruction':'PASS','deliberate_electron_count_corruption':'REJECTED_AS_EXPECTED','scope':'Analyzer controls, not drug validation'},indent=2)+'\n')
print('PASS actual-water checkpoint analysis and deliberate electron-count rejection')
