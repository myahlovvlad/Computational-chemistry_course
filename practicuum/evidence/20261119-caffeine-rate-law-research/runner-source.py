"""Audit the published caffeine hydroxide rate law; no invented time series."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from scipy import stats


def rate_law(oh, rates):
    """OLS on five published rate estimates; uncertainty is conditional on OLS assumptions."""
    x = np.asarray(oh, dtype=float)
    y = np.asarray(rates, dtype=float)
    if x.ndim != 1 or y.shape != x.shape or len(x) < 4:
        raise ValueError('At least four paired concentrations and rates required')
    if not (np.isfinite(x).all() and np.isfinite(y).all() and (x > 0).all() and (y > 0).all()):
        raise ValueError('Finite positive concentrations and rates required')
    X = np.column_stack([np.ones(len(x)), x])
    if np.linalg.matrix_rank(X) != 2:
        raise ValueError('Concentrations do not identify a slope')
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    residual = y-X@beta
    df = len(y)-2
    covariance = (residual@residual/df)*np.linalg.inv(X.T@X)
    ci = np.column_stack([beta-stats.t.ppf(.975, df)*np.sqrt(np.diag(covariance)),
                          beta+stats.t.ppf(.975, df)*np.sqrt(np.diag(covariance))])
    leverage = np.einsum('ij,jk,ik->i', X, np.linalg.inv(X.T@X), X)
    constrained = float(x@y/(x@x))
    sse0 = float(np.sum((y-constrained*x)**2))
    sse = float(residual@residual)
    f = max(0., (sse0-sse)/(sse/df)) if sse > 0 else None
    return {'intercept_min_inverse': float(beta[0]), 'k2_L_mol_inverse_min_inverse': float(beta[1]),
            'conditional_OLS_CI95': ci.tolist(), 'residuals_min_inverse': residual.tolist(),
            'leverage': leverage.tolist(), 'residual_degrees_freedom': df,
            'leave_one_concentration_out_RMSE_min_inverse': float(np.sqrt(np.mean((residual/(1-leverage))**2))),
            'through_origin_k2_L_mol_inverse_min_inverse': constrained,
            'intercept_F_test': {'F': f, 'df': [1, df], 'p': None if f is None else float(stats.f.sf(f, 1, df))},
            'uncertainty_scope': 'Conditional homoscedastic independent rate-estimate OLS; published Table 4 has no replicate errors. These are not experimental confidence limits.',
            'raw_time_series_refit': 'NOT_RUN', 'lack_of_fit_test': 'NOT_IDENTIFIABLE: no replicated concentrations'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    raw = args.source.read_bytes(); root = ET.fromstring(raw)
    if not any(n.text == '10.1186/s40064-015-0809-x' for n in root.findall('.//article-id')):
        raise ValueError('Unexpected article')
    if not any('creativecommons.org/licenses/by/4.0' in ''.join(n.itertext()) for n in root.findall('.//license')):
        raise ValueError('Licence unverified')
    table = root.find('.//table-wrap[@id="Tab4"]')
    rows = [[float(''.join(c.itertext()).strip()) for c in tr] for tr in table.findall('.//tr')[1:]]
    if len(rows) != 5 or any(len(r) != 3 for r in rows):
        raise ValueError('Unexpected Table 4 layout')
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    with (out/'caffeine_hydroxide_table4.csv').open('x', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream); writer.writerow(['NaOH_mol_L', 'kexp_min_inverse', 'reported_half_life_min'])
        writer.writerows(rows)
    fit = rate_law([r[0] for r in rows], [r[1] for r in rows])
    fit['half_life_rounding_error_min'] = [float(np.log(2)/r[1]-r[2]) for r in rows]
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    x = np.array([r[0] for r in rows]); y = np.array([r[1] for r in rows])
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
    axes[0].plot(x, y, 'o', label='Published Table 4')
    axes[0].plot(x, fit['intercept_min_inverse']+fit['k2_L_mol_inverse_min_inverse']*x, label='OLS with intercept')
    axes[0].plot(x, fit['through_origin_k2_L_mol_inverse_min_inverse']*x, '--', label='Through origin')
    axes[0].set(xlabel='NaOH / mol L^-1', ylabel='k_exp / min^-1'); axes[0].legend(fontsize=7)
    axes[1].axhline(0, color='gray'); axes[1].plot(x, fit['residuals_min_inverse'], 'o-')
    axes[1].set(xlabel='NaOH / mol L^-1', ylabel='OLS residual / min^-1')
    fig.tight_layout(); fig.savefig(out/'rate_law.png', dpi=160); plt.close(fig)
    report = {'status': 'PASS', 'scope': 'reanalysis of published rate estimates, not new measurements',
              'created_utc': datetime.now(timezone.utc).isoformat(),
              'source': {'doi': '10.1186/s40064-015-0809-x', 'authors': 'Edwards, Kulikov, Garner-O’Neale (2015)',
                         'licence': 'CC BY 4.0', 'url': 'https://link.springer.com/article/10.1186/s40064-015-0809-x',
                         'sha256': hashlib.sha256(raw).hexdigest(),
                         'conditions': '100 C; initially 25 mg/L caffeine; GC-MS/MS-MRM; NaOH 0.02–0.10 mol/L'},
              'fit': fit, 'scientific_review': 'NOT_RUN',
              'limitations': ['Caffeine is a xanthine-family case, not istradefylline kinetics',
                              'Table 5 rates at 30 C are author extrapolations, not independent observations',
                              'The prose unit for second-order k is dimensionally inconsistent; the rate law requires L mol^-1 min^-1',
                              'Alkaline thermal hydrolysis cannot establish physiological or environmental total disappearance']}
    (out/'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    (out/'primary-source.xml').write_bytes(raw)
    (out/'runner-source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(fit, indent=2))


if __name__ == '__main__':
    main()
