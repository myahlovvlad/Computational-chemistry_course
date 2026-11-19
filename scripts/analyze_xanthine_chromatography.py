"""Reanalyse published methylxanthine UHPLC ruggedness without fabricated chromatograms."""
import argparse,csv,hashlib,json,re
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy import stats


def extract(source):
    raw=Path(source).read_bytes();doc=ET.fromstring(raw)
    if not any(n.text=='10.1155/2019/2926580' for n in doc.findall('.//article-id')):raise ValueError('Wrong publication')
    if not any('Creative Commons Attribution License' in ''.join(n.itertext()) for n in doc.findall('.//license')):
        raise ValueError('Reuse licence missing')
    table=doc.find('.//table-wrap[@id="tab4"]')
    rows=[]
    for tr in table.findall('.//tr'):
        cells=[''.join(c.itertext()).strip() for c in tr]
        if len(cells)!=3:continue
        match=re.fullmatch(r'([0-9.]+)\s*±\s*([0-9.]+)',cells[1])
        if match:
            rows.append({'condition':cells[0],'retention_s':float(match[1]),'RSD_percent':float(match[2]),'n':3,
                         'reported_change_percent':None if cells[2]=='—' else float(cells[2])})
    if len(rows)!=7:raise ValueError('Unexpected Table 4 layout')
    factors=[[10,70,.5],[10,70,.55],[10,70,.45],[15,70,.5],[5,70,.5],[10,75,.5],[10,65,.5]]
    for row,(acn,temp,flow) in zip(rows,factors):
        row.update(ACN_percent=acn,temperature_C=temp,flow_mL_min=flow)
    return raw,rows


def diagnostics(rows):
    t=np.array([r['retention_s'] for r in rows]);rsd=np.array([r['RSD_percent'] for r in rows]);n=np.array([r['n'] for r in rows])
    sd=t*rsd/100
    half=stats.t.ppf(.975,n-1)*sd/np.sqrt(n)
    factor=np.array([[r[k] for k in ['ACN_percent','temperature_C','flow_mL_min']] for r in rows])
    coded=(factor-[10,70,.5])/[5,5,.05]
    X=np.column_stack([np.ones(len(t)),coded,coded*coded,coded[:,0]*coded[:,1],coded[:,0]*coded[:,2],coded[:,1]*coded[:,2]])
    full_rank=int(np.linalg.matrix_rank(X))
    additive=X[:,:7];beta=np.linalg.lstsq(additive,t,rcond=None)[0]
    return {'n_conditions':len(t),'full_quadratic_columns':X.shape[1],'full_quadratic_rank':full_rank,
            'unidentifiable_interaction_columns':np.flatnonzero(np.all(X==0,axis=0)).tolist(),
            'additive_quadratic_rank':int(np.linalg.matrix_rank(additive)),
            'additive_model_condition_mean_residual_df':len(t)-int(np.linalg.matrix_rank(additive)),
            'additive_coefficients_s':beta.tolist(),'derived_SD_s':sd.tolist(),
            'conditional_mean_CI95_s':np.column_stack([t-half,t+half]).tolist(),
            'relative_retention_change_percent':(100*(t-t[0])/t[0]).tolist(),
            'pure_error_SS_from_reported_summary':float(np.sum((n-1)*sd**2)),
            'pure_error_df':int(np.sum(n-1)),
            'uncertainty_scope':'Conditional independent normal n=3 repeats; %RSD is not absolute SD. Raw repeats and independence unit are unavailable.',
            'interaction_optimization':'BLOCKED: OFAT never varies two factors together',
            'lack_of_fit':'NOT_IDENTIFIABLE for saturated additive quadratic condition means',
            'measured_resolution':'NOT_CALCULABLE: numerical baseline peak widths absent'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    raw,rows=extract(args.source);report=diagnostics(rows)
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    with (out/'xanthine_uhplc_ruggedness.csv').open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    source={'doi':'10.1155/2019/2926580','title':'Rapid and Sensitive Determination of Methylxanthines in Commercial Brands of Tea Using Ultra-High-Performance Liquid Chromatography-Mass Spectrometry',
            'url':'https://doi.org/10.1155/2019/2926580','licence':'Creative Commons Attribution; version unspecified in retrieved XML; preserve original licence text',
            'source_sha256':hashlib.sha256(raw).hexdigest(),
            'conditions':'Table 2: Nucleodur C18 polar Tec 50 x 2 mm, 1.8 um; ACN/water 10:90 with 1% formic acid; 0.5 mL/min; 70 C; 5 uL; ESI+ SIM',
            'reported_baseline_retention_s':{'theobromine':14,'theophylline':19,'caffeine':28},
            'scope':'tea methylxanthines; not istradefylline, atorvastatin or pharmaceutical-matrix validation'}
    result={'status':'PASS','scope':'actual reanalysis of published means and %RSD, not new UHPLC injections',
            'source':source,'diagnostics':report,'scientific_review':'NOT_RUN','prospective_method_validation':'NOT_RUN'}
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (out/'primary-source.xml').write_bytes(raw);(out/'runner-source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
