"""Publication-data RSM with pure error, lack of fit, grouped validation and uncertainty.

No invented peak widths, resolution, chromatographic signals or experimental runs.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy import stats

ROOT=Path(__file__).resolve().parents[1]
FACTORS=['acetonitrile_percent','column_temperature_C','flow_mL_min']
TERMS=['intercept','ACN','temperature','flow','ACN^2','temperature^2','flow^2','ACN:temperature','ACN:flow','temperature:flow']


def design(factors):
    x=(np.asarray(factors)-[65,35,1])/[5,5,.2]
    return np.column_stack([np.ones(len(x)),x,x*x,x[:,0]*x[:,1],x[:,0]*x[:,2],x[:,1]*x[:,2]])


def fit_response(factors,y,alpha=.05):
    X=design(factors);n,p=X.shape;rank=int(np.linalg.matrix_rank(X))
    if rank!=p or n<=p:raise ValueError('Full-rank replicated design required')
    beta=np.linalg.lstsq(X,y,rcond=None)[0];fitted=X@beta;residual=y-fitted
    SSE=float(residual@residual);mse=SSE/(n-p)
    unique,group=np.unique(factors,axis=0,return_inverse=True)
    pure_error=sum(float(np.sum((y[group==i]-np.mean(y[group==i]))**2)) for i in range(len(unique)))
    df_pure=n-len(unique);df_lof=len(unique)-p
    if df_pure<=0 or df_lof<=0:raise ValueError('Insufficient replicate or lack-of-fit degrees of freedom')
    lack_of_fit=SSE-pure_error
    if lack_of_fit < -1e-10:raise ArithmeticError('SSE < pure error')
    lack_of_fit=max(0,lack_of_fit)
    if pure_error>0:
        F=(lack_of_fit/df_lof)/(pure_error/df_pure);pvalue=float(stats.f.sf(F,df_lof,df_pure))
    else:
        F=None;pvalue=None
    # Validation unit is a complete experimental condition, including every replicate.
    heldout=np.full(n,np.nan);folds=[]
    for g in range(len(unique)):
        test=group==g;train=~test;foldrank=int(np.linalg.matrix_rank(X[train]))
        if foldrank==p:heldout[test]=X[test]@np.linalg.lstsq(X[train],y[train],rcond=None)[0]
        folds.append({'condition':unique[g].tolist(),'test_row_ids':np.flatnonzero(test).tolist(),
                      'train_row_ids':np.flatnonzero(train).tolist(),'rank':foldrank,
                      'status':'PASS' if foldrank==p else 'BLOCKED_RANK_DEFICIENT'})
    cv_valid=bool(np.isfinite(heldout).all())
    covariance=mse*np.linalg.inv(X.T@X);critical=float(stats.t.ppf(1-alpha/2,n-p))
    standard_errors=np.sqrt(np.diag(covariance))
    center=np.array([1.,0,0,0,0,0,0,0,0,0]);center_prediction=float(center@beta)
    center_h=float(center@np.linalg.solve(X.T@X,center))
    leverage=np.sum(X*np.linalg.solve(X.T@X,X.T).T,axis=1)
    studentized=residual/np.sqrt(mse*np.maximum(1-leverage,1e-15))
    cook=(residual**2/(p*mse))*leverage/(np.maximum(1-leverage,1e-15)**2)
    return {'terms':TERMS,'coefficients':beta.tolist(),'coefficient_SE':standard_errors.tolist(),
      'coefficient_CI95':np.column_stack([beta-critical*standard_errors,beta+critical*standard_errors]).tolist(),
      'n':n,'p':p,'rank':rank,'condition_number':float(np.linalg.cond(X)),
      'residual_df':n-p,'SSE':SSE,'MSE':mse,'pure_error_SS':pure_error,'pure_error_df':df_pure,
      'lack_of_fit_SS':lack_of_fit,'lack_of_fit_df':df_lof,'lack_of_fit_F':F,'lack_of_fit_p':pvalue,
      'lack_of_fit_detected':None if pvalue is None else pvalue<alpha,
      'adequacy':'REJECTED_LACK_OF_FIT' if pvalue is not None and pvalue<alpha else 'NOT_REJECTED_NOT_VALIDATED',
      'train_RMSE':float(np.sqrt(np.mean(residual**2))),
      'held_condition_RMSE':float(np.sqrt(np.mean((heldout-y)**2))) if cv_valid else None,
      'held_condition_MAE':float(np.mean(abs(heldout-y))) if cv_valid else None,
      'held_condition_status':'PASS' if cv_valid else 'BLOCKED_RANK_DEFICIENT',
      'observed':y.tolist(),'fitted':fitted.tolist(),'held_condition_prediction':np.where(np.isfinite(heldout),heldout,0).tolist(),
      'residuals':residual.tolist(),'leverage':leverage.tolist(),'studentized_residuals':studentized.tolist(),'Cooks_D':cook.tolist(),
      'center_estimated_mean':center_prediction,
      'center_mean_CI95':[center_prediction-critical*np.sqrt(mse*center_h),center_prediction+critical*np.sqrt(mse*center_h)],
      'center_new_injection_PI95':[center_prediction-critical*np.sqrt(mse*(1+center_h)),center_prediction+critical*np.sqrt(mse*(1+center_h))],
      'interval_assumptions':'correct quadratic mean, independent homoscedastic normal errors; not valid if model is inadequate',
      'folds':folds,'covariance':covariance.tolist()}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    source=ROOT/'practicuum/shared/data/atorvastatin_hplc_table1.csv'
    provenance=json.loads((source.parent/'hplc_provenance.json').read_text(encoding='utf-8'))
    with source.open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
    factors=np.array([[float(r[k]) for k in FACTORS] for r in rows])
    if not np.isfinite(factors).all():raise ValueError('Nonfinite factor')
    responses=[key for key in rows[0] if key not in FACTORS]
    models={}
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for key in responses:
        y=np.array([float(r[key]) for r in rows]);model=fit_response(factors,y);models[key]=model
        fig,axes=plt.subplots(1,3,figsize=(13,4))
        axes[0].scatter(model['fitted'],model['residuals']);axes[0].axhline(0,color='gray')
        axes[0].set(xlabel='Fitted response (source units)',ylabel='Residual (source units)')
        stats.probplot(model['studentized_residuals'],plot=axes[1]);axes[1].set_title('Residual normal Q-Q (diagnostic)')
        axes[2].scatter(model['leverage'],model['studentized_residuals'])
        axes[2].set(xlabel='Leverage',ylabel='Internally studentized residual')
        fig.suptitle(key+' · '+model['adequacy']);fig.tight_layout();fig.savefig(out/(key+'.png'),dpi=150);plt.close(fig)
        print(key,model['adequacy'],'LOF p=',model['lack_of_fit_p'],'held-condition RMSE=',model['held_condition_RMSE'],flush=True)
    report={'status':'PASS','scope':'actual reanalysis of published experiments; not new chromatography measurements',
      'source':provenance,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
      'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'python':sys.version,
      'factor_names':FACTORS,'factor_coding':{'center':[65,35,1],'scale':[5,5,.2]},'factors':factors.tolist(),
      'models':models,'measured_Rs':'NOT_CALCULABLE: baseline widths unavailable',
      'method_optimization':'NOT_ACCEPTED: prospective experiment and all analytical constraints required',
      'limitations':['Small original experiment, not external validation','Repeated injections do not establish independent sample-preparation uncertainty',
                     'LOF tests are per-response diagnostics; not adjusted for multiple comparisons','Prediction intervals are conditional on model adequacy',
                     'No extrapolation in pH, column, sample matrix or elution mode','No invented raw chromatograms, LOD, LOQ or peak widths'],
      'scientific_review':'NOT_RUN'}
    (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (out/'source.csv').write_bytes(source.read_bytes());(out/'runner-source.py').write_bytes(Path(__file__).read_bytes())


if __name__=='__main__':main()
