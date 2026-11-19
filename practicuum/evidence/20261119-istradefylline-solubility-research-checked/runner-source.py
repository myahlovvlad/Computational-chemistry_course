"""Extract visually checked Table S1 and audit solubility bases before inference.

Requires the public Wang et al. PDF/ZIP snapshot and Poppler pdftotext.
No missing replicate errors or solvent densities are fabricated.
"""
import argparse,csv,hashlib,json,re,subprocess,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy import stats

SOLVENTS=['methanol','ethanol','ethyl acetate','n-propanol','isopropanol','n-butanol','acetonitrile',
          'methanol/water 30/70 v/v','ethanol/water 24/76 v/v','ethanol/water 55/45 v/v',
          'acetonitrile/water 25/75 v/v','acetonitrile/water 58/42 v/v']
FORMS=['II','I','I','I','I','I','III','II','I','I','III','III']
MW=384.43


def extract_table(pdf,bbox):
    process=subprocess.run(['pdftotext','-bbox',str(pdf),str(bbox)],capture_output=True)
    if process.returncode:raise RuntimeError(process.stderr.decode(errors='replace'))
    ns={'h':'http://www.w3.org/1999/xhtml'};doc=ET.parse(bbox);rows=[]
    for page_index,page in enumerate(doc.findall('.//h:page',ns)[:2],1):
        words=[(float(w.get('xMin')),float(w.get('yMin')),w.text or '') for w in page.findall('h:word',ns)]
        temperatures=sorted((w for w in words if 155<w[0]<190 and (page_index!=1 or w[1]>210)
                             and w[2] in {'293.15','303.15','313.15','323.15','333.15'}),key=lambda w:w[1])
        for _,y,temp in temperatures:
            def cell(low,high):
                return ''.join(w[2] for w in sorted(words,key=lambda w:w[0]) if low<w[0]<high and abs(w[1]-y)<.7).replace('−','-')
            def scientific(s):
                match=re.fullmatch(r'([0-9.]+)∙10(-?[0-9]+)',s)
                if not match:raise ValueError('Unparsed scientific cell '+repr(s))
                return float(match[1])*10**int(match[2])
            x=scientific(cell(195,255));xcalc=scientific(cell(260,315))
            deviation=float(cell(320,365));mass=float(cell(370,420))
            if not 0<x<1 or not 0<xcalc<1 or mass<=0:raise ValueError('Nonphysical table value')
            group=len(rows)//5
            if group>=len(SOLVENTS):raise ValueError('Unexpected extra table rows')
            rows.append({'solvent':SOLVENTS[group],'temperature_K':float(temp),'x_as_reported':x,
                         'x_calculated_by_authors':xcalc,'relative_deviation_percent_as_reported':deviation,
                         'solubility_mg_mL_as_reported':mass,'equilibrium_form_as_reported':FORMS[group],
                         'supporting_PDF_page':page_index})
    if len(rows)!=60:raise ValueError('Expected 12 solvents x 5 temperatures, received '+str(len(rows)))
    for i in range(12):
        if [r['temperature_K'] for r in rows[i*5:(i+1)*5]]!=[293.15,303.15,313.15,323.15,333.15]:
            raise ValueError('Temperature/solvent grouping changed')
    return rows


def vanthoff(T,x):
    T=np.asarray(T,dtype=float);x=np.asarray(x,dtype=float)
    if not (T.shape==x.shape and T.ndim==1 and len(T)>=4 and np.isfinite(T).all() and np.isfinite(x).all() and (T>0).all() and (x>0).all()):
        raise ValueError('Positive finite paired temperatures/solubilities required')
    z=1000/T;X=np.column_stack([np.ones(len(T)),z-z.mean()]);y=np.log(x)
    if np.linalg.matrix_rank(X)!=2:raise ValueError('Temperature variation required')
    beta=np.linalg.lstsq(X,y,rcond=None)[0];residual=y-X@beta;df=len(y)-2
    inverse=np.linalg.inv(X.T@X);mse=float(residual@residual/df)
    se=np.sqrt(np.diag(mse*inverse));critical=stats.t.ppf(.975,df)
    h=np.einsum('ij,jk,ik->i',X,inverse,X)
    # z=1000/T: d ln(x)/d(1/T)=1000*b; -R*1000*b/1000 gives kJ/mol.
    apparent=-8.31446261815324*beta[1]
    half=8.31446261815324*critical*se[1]
    return {'intercept_at_mean_inverse_temperature':float(beta[0]),'slope_per_1000_K_inverse':float(beta[1]),
            'apparent_slope_enthalpy_kJ_mol':float(apparent),
            'conditional_CI95_kJ_mol':[float(apparent-half),float(apparent+half)],
            'residuals_ln_x':residual.tolist(),'leave_one_temperature_out_RMSE_ln_x':float(np.sqrt(np.mean((residual/(1-h))**2))),
            'fitted_ln_x':(X@beta).tolist(),'df':df,
            'interpretation':'Conditional apparent slope of the reported solubility basis; not a measured thermodynamic dissolution enthalpy. Activities, solvate equilibria, raw repeats and independent data remain unverified.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-dir',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    card=json.loads((args.source_dir/'provenance.json').read_text(encoding='utf-8'))
    if card['doi']!='10.3390/cryst12070917':raise ValueError('Wrong primary study')
    for record in card['sources']:
        if hashlib.sha256((args.source_dir/record['file']).read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError('Changed primary source '+record['file'])
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(args.source_dir/'crystals-12-00917-s001.zip') as archive:
        files=[n for n in archive.namelist() if n.lower().endswith('.pdf')]
        if len(files)!=1:raise ValueError('Unambiguous supporting PDF required')
        pdf=out/'supporting-information.pdf';pdf.write_bytes(archive.read(files[0]))
    rows=extract_table(pdf,out/'table-bbox.html')
    with (out/'istradefylline_solubility_table_S1.csv').open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    fits=[];diagnostics=[]
    for i,solvent in enumerate(SOLVENTS):
        group=rows[i*5:(i+1)*5];T=[r['temperature_K'] for r in group];x=np.array([r['x_as_reported'] for r in group])
        mass=np.array([r['solubility_mg_mL_as_reported'] for r in group]);calculated=np.array([r['x_calculated_by_authors'] for r in group])
        reported=np.array([r['relative_deviation_percent_as_reported'] for r in group]);derived=100*abs(calculated-x)/x
        # mg/mL numerically equals g/L. This diagnostic assumes the mass column
        # describes istradefylline equivalents and x is an ordinary mole fraction.
        implied_solvent_molarity=(mass/MW)*(1-x)/x
        row={'solvent':solvent,'equilibrium_form_as_reported':FORMS[i],
             'mole_fraction_fit':vanthoff(T,x),'mass_concentration_fit':vanthoff(T,mass)}
        fits.append(row)
        diagnostics.append({'solvent':solvent,'temperatures_K':T,'recomputed_relative_deviation_percent':derived.tolist(),
            'reported_relative_deviation_percent':reported.tolist(),
            'deviation_difference_exceeds_0_05_percentage_points':(abs(derived-reported)>.05).tolist(),
            'implied_solvent_molarity_mol_L':implied_solvent_molarity.tolist(),
            'implied_molarity_relative_to_293K':(implied_solvent_molarity/implied_solvent_molarity[0]).tolist(),
            'assessment':'REVIEW: compare both concentration bases and formula/dilution/solid-form definitions with original raw data. No density was imputed.'})
    # Table 2 was visually checked against main PDF p.7; explicit manual
    # transcription avoids pretending that a fitted or digitised curve was measured.
    ph=[1,2,3,4,7,8,10,12];S=[.41,.39,.32,.31,.27,.18,.11,.10]
    with (out/'istradefylline_aqueous_pH_table2.csv').open('x',encoding='utf-8',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['pH','temperature_K','solubility_ug_mL_as_reported'])
        writer.writerows((p,293.15,s) for p,s in zip(ph,S))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,4,figsize=(14,10))
    for ax,fit in zip(axes.flat,fits):
        group=[r for r in rows if r['solvent']==fit['solvent']];z=1000/np.array([r['temperature_K'] for r in group])
        ax.plot(z,np.log([r['x_as_reported'] for r in group]),'o',label='Published x')
        ax.plot(z,fit['mole_fraction_fit']['fitted_ln_x'],label='Conditional fit')
        ax.set(title=fit['solvent'],xlabel='1000 / T [K^-1]',ylabel='ln x');ax.tick_params(labelsize=8)
    fig.tight_layout();fig.savefig(out/'conditional_vanthoff.png',dpi=150);plt.close(fig)
    result={'status':'PASS','scope':'actual primary table extraction, conditional regression and numerical consistency audit',
            'source':card,'supporting_PDF_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),
            'table_extraction':'Poppler bounding boxes; visually checked supporting PDF pages 1/2 and main PDF p.7',
            'visual_review':'table headings, exponents, mass units and crystal-form labels inspected',
            'source_data_acceptance':'REVIEW_REQUIRED','fits':fits,'basis_diagnostics':diagnostics,
            'aqueous_pH_diagnostics':{'reported_ug_mL':S,'molarity_API_equivalents':[s*.001/MW for s in S],
                'main_article_calibration_range_mg_mL':[.001,.1],
                'below_stated_calibration_range_without_documented_preconcentration':[s*.001<.001 for s in S],
                'assessment':'REVIEW: verify aqueous quantification LOQ/calibration and any concentration step; do not fit a pKa or label an intrinsic S0 without phase and analytical validation'},
            'limitations':['100 delta is model relative deviation, not replicate SD; do not use it as a measurement weight',
                'Three repeats are reported in methods, but individual data/SD are unavailable',
                'Reported mole fraction and mass concentration remain separate; apparent slope differences need source review',
                'Mixed-solvent composition basis and solvate/hydrate equilibrium require explicit thermodynamic treatment',
                'No extrapolation outside 293.15–333.15 K or claim of bioavailability'],
            'scientific_review':'NOT_RUN'}
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (out/'runner-source.py').write_bytes(Path(__file__).read_bytes())
    print('Extracted',len(rows),'published observations; source acceptance REVIEW_REQUIRED')
    print('Methanol apparent slopes, x and mass:',fits[0]['mole_fraction_fit']['apparent_slope_enthalpy_kJ_mol'],fits[0]['mass_concentration_fit']['apparent_slope_enthalpy_kJ_mol'])


if __name__=='__main__':main()
