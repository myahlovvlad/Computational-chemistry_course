from pathlib import Path
import json,xml.etree.ElementTree as ET
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'programm/course.json').is_file())
doc=ET.parse(ROOT/'practicuum/shared/data/source-responses/statin_stability_verified.xml')
rows=[[''.join(c.itertext()).strip() for c in r] for r in doc.findall('.//table-wrap[@id="pharmaceutics-17-00808-t011"]//tr')][1:]
S0=float(rows[0][2]);K1=float(rows[0][4]);K2=float(rows[1][4])
result={'HPbetaCD_conditional_slope':K1*S0/(1+K1*S0),'gammaCD_conditional_slope':K2*S0/(1+K2*S0),'HPbetaCD_linear_model_accepted_without_review':False,'new_fit':'NOT_RUN'}
if __name__=='__main__':print(json.dumps(result,indent=2))
