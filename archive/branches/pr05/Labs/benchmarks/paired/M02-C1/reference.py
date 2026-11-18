scale={'M':1,'mM':1e-3,'uM':1e-6,'nM':1e-9}; p=[]; statuses=[]
for v,u in zip(case_input['values'],case_input['units']):
    valid=u in scale and math.isfinite(v) and v>0
    p.append(-math.log10(v*scale[u]) if valid else None); statuses.append('ok' if valid else 'invalid')
answer={'p_values':p,'statuses':statuses}