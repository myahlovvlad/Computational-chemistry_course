"""Reanalyse published atorvastatin kinetic and phase-solubility parameters without invented observations."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]


def table_rows(doc,id):
    table=doc.find('.//table-wrap[@id="'+id+'"]')
    if table is None:raise ValueError('Missing primary table '+id)
    return [[''.join(c.itertext()).strip() for c in row if c.tag in {'td','th'}] for row in table.findall('.//tr')]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();raw=args.source.read_bytes();doc=ET.fromstring(raw)
    if not any(n.text=='10.3390/pharmaceutics17070808' for n in doc.findall('.//article-id')):raise ValueError('Wrong article DOI')
    if not any('creativecommons.org/licenses/by/4.0' in ''.join(n.itertext()) for n in doc.findall('.//license')):raise ValueError('Reuse licence not verified')
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    kinetic=table_rows(doc,'pharmaceutics-17-00808-t001')[2:]
    if len(kinetic)!=4 or any(len(r)!=10 for r in kinetic):raise ValueError('Unexpected kinetic table layout')
    data=[]
    for row in kinetic:
        for pH,value in zip([2.,4.5,7.,9.5],row[6:10]):
            rate=None if value.strip()=='-' else float(value)
            data.append({'initial_form':row[0],'parameter_as_published':row[1],'pH':pH,
                'reported_rate_h_inverse':rate,'reported_rate_text':value,
                'uncertainty':'not reported for atorvastatin in this table',
                'apparent_half_relaxation_hours':None if rate is None else math.log(2)/rate})
    comparisons=[]
    for form,pair in [('Ring-closed',(0,1)),('Ring-opened',(2,3))]:
        for col,pH in enumerate([2.,4.5,7.,9.5],6):
            a,b=kinetic[pair[0]][col],kinetic[pair[1]][col]
            if '-' in {a,b}:continue
            a,b=float(a),float(b)
            comparisons.append({'initial_form':form,'pH':pH,'reported_parameter_1':a,'reported_parameter_2':b,
                'ratio_2_to_1':b/a,'relative_discrepancy_to_mean':abs(a-b)/((a+b)/2),
                'assessment':'shared relaxation constant requires scrutiny; no raw data/uncertainties for a statistical rejection'})
    solubility=table_rows(doc,'pharmaceutics-17-00808-t011')[1:];phase=[]
    for row in solubility:
        if len(row)!=6:raise ValueError('Unexpected phase-solubility table layout')
        S=float(row[2]);K=float(row[4]);CE=float(row[5]);derived=K*S
        phase.append({'formulation':row[0],'pH':float(row[1]),'S0_as_reported_mol_L':S,
            'phase_solubility_type':row[3],'K_1_1_as_reported_M_inverse':K,'CE_as_reported':CE,
            'K_times_S0':derived,'CE_relative_difference':(derived-CE)/CE,
            'linear_1_to_1_implied_slope':derived/(1+derived),
            'applicability':'A_N curvature means linear 1:1 analysis requires independent validation' if row[3]=='AN' else 'conditional linear 1:1 relation; raw slope uncertainty unavailable',
            'molar_basis':'paper-reported baseline at pH 6.9; do not identify automatically with intrinsic neutral-acid solubility or convert salt units silently'})
    # Algebraic control of mechanistic identifiability, not a new kinetic fit:
    # for L <-> A, lambda = kopen + kclose and Aeq/(L+A) = kopen/lambda.
    # Apparent single-exponential constants alone leave infinitely many microscopic pairs.
    identification={'equations':['dL/dt=-kopen*L+kclose*A','dA/dt=kopen*L-kclose*A',
       'lambda=kopen+kclose','acid_equilibrium_fraction=kopen/lambda'],
       'conclusion':'Published independently fitted apparent rate constants cannot automatically be assigned as microscopic forward/reverse rates',
       'required_for_new_fit':['raw paired concentration-time observations','form-specific detector response and mass balance',
          'replicate structure and uncertainty','baseline/plateau estimates','parameter covariance and model comparison'],
       'new_fit_status':'NOT_RUN: numerical raw concentration-time observations are not supplied here'}
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(8,5))
    for i in range(4):
        row=data[i*4:(i+1)*4];valid=[r for r in row if r['reported_rate_h_inverse'] is not None]
        ax.semilogy([r['pH'] for r in valid],[r['reported_rate_h_inverse'] for r in valid],'o-',label=valid[0]['parameter_as_published'])
    ax.set(xlabel='Buffer pH',ylabel='Published apparent rate constant / h^-1',title='Atorvastatin · Table 1 · no new kinetic fit')
    ax.legend(fontsize=8);fig.tight_layout();fig.savefig(out/'published_rates.png',dpi=160);plt.close(fig)
    report={'status':'PASS','scope':'actual consistency/identifiability analysis of published atorvastatin parameters',
       'source':{'authors':'Abo Horan, Loftsson, Sigurdsson (2025)','doi':'10.3390/pharmaceutics17070808',
          'url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC12300459/','licence':'CC BY 4.0','source_sha256':hashlib.sha256(raw).hexdigest(),
          'conditions':'0.15 M universal buffer; 0% CD for Table 1; 23 +/-1 C; atorvastatin measurements lack reported replicate uncertainty in Table 1',
          'distinct_scope':'aqueous ocular formulation study; not hepatic exposure or pharmacokinetics'},
       'kinetic_parameters':data,'paired_rate_diagnostics':comparisons,'phase_solubility_diagnostics':phase,
       'kinetic_identifiability':identification,'scientific_review':'NOT_RUN',
       'not_inferred':['missing rate is not zero','apparent half-relaxation time is not automatically half-disappearance of a reversible species',
                       'reported baseline S0 at buffer pH is not intrinsic neutral-species solubility','published formulation parameters do not establish liver delivery']}
    (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (out/'primary-source.xml').write_bytes(raw);(out/'runner-source.py').write_bytes(Path(__file__).read_bytes())
    print('Atorvastatin published parameters:',len(data),'paired-rate diagnostics:',len(comparisons),'phase-solubility formulations:',len(phase))
    print('pH 4.5 loss/formation discrepancy:',next(r['ratio_2_to_1'] for r in comparisons if r['pH']==4.5 and r['initial_form']=='Ring-closed'))
    print('New fit NOT_RUN: raw observations absent; missing constants not replaced by zeros')


if __name__=='__main__':main()
