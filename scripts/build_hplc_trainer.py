"""Подготовить собственную регрессию по опубликованной таблице; не восстанавливает сырые сигналы."""
from pathlib import Path
import csv,hashlib,json
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'practicuum/shared/data'
TARGET=ROOT/'web-training/trainers/hplc'

def main():
    source=DATA/'atorvastatin_hplc_table1.csv'
    with source.open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
    factors=['acetonitrile_percent','column_temperature_C','flow_mL_min']
    responses=['retention_p_ATO_min','retention_ATO_lactone_min']
    x=np.array([[float(row[key]) for key in factors] for row in rows])
    z=(x-np.array([65,35,1]))/np.array([5,5,.2])
    a,b,c=z.T
    # Полный квадратичный отклик: главные, парные и квадратичные члены.
    design=np.column_stack([np.ones(len(x)),a,b,c,a*b,a*c,b*c,a*a,b*b,c*c])
    y=np.array([[float(row[key]) for key in responses] for row in rows])
    beta,residuals,rank,singular=np.linalg.lstsq(design,y,rcond=None)
    if rank!=10:raise ValueError('Матрица плана не имеет требуемого ранга')
    result={'source_doi':'10.3390/molecules18032469',
      'attribution':'Crevar-Sakač, Vujić, Brborić, Kuntić, Uskoković-Marković (2013), Table 1; CC BY 3.0',
      'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
      'method':'own full quadratic ordinary least squares refit; not exact reconstruction of published reduced models',
      'factor_order':factors,'center':[65,35,1],'scale':[5,5,.2],
      'terms':['1','a','b','c','a*b','a*c','b*c','a*a','b*b','c*c'],
      'response_order':responses,'coefficients':beta.tolist(),'rank':int(rank),'n':len(rows),
      'training_RMSE_min':np.sqrt(np.mean((design@beta-y)**2,axis=0)).tolist(),
      'validation':'in-sample fit only; independent validation NOT_RUN',
      'fixed_conditions':{'pH':4.6,'column':'ZORBAX Eclipse Plus C18 250 x 4.6 mm, 5 um',
                          'elution':'isocratic','detector_nm':254,'sample_matrix':'Wistar rat plasma'},
      'observations':[{k:float(v) for k,v in row.items()} for row in rows],
      'figure5_annotated_Rt_min':{'p_ATO':3.052,'o_ATO':4.780,'ATO':5.445,'ATO_lactone':7.064},
      'figure5_conditions':{'ACN_percent':61.93,'temperature_C':31.44,'flow_mL_min':1.03},
      'figure5_scope':'one published chromatogram; annotations are not numeric raw traces or a fitted model of middle peaks',
      'limitations':['no numeric raw chromatograms','no baseline peak widths',
        'middle-peak positions outside the single figure condition are assumptions',
        'all Gaussian profiles and widths in the trainer are explicit teaching simulations',
        'no pH/gradient/column response calibration','Rs alone does not establish method validation']}
    TARGET.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(result,ensure_ascii=False,indent=2)
    (TARGET/'model.json').write_text(payload,encoding='utf-8')
    # Локальная страница открывается и через file://: fetch/server для модели не нужен.
    (TARGET/'model.js').write_text('window.HPLC_MODEL = '+payload+';\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['n','rank','training_RMSE_min','input_sha256']},indent=2))

if __name__=='__main__':main()
