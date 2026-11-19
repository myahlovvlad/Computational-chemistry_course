from pathlib import Path
import json,math,sys
import xml.etree.ElementTree as ET
import numpy as np
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'programm/course.json').is_file())
doc=ET.parse(ROOT/'practicuum/shared/data/source-responses/statin_stability_verified.xml')
rows=[[''.join(c.itertext()).strip() for c in r] for r in doc.findall('.//table-wrap[@id="pharmaceutics-17-00808-t001"]//tr')][2:]
slow=float(rows[0][7]);fast=float(rows[1][7])
u,v=.4,.6  # Algebraic point; NOT measured microscopic rates.
J1=np.array([[1.,1.]])
J2=np.array([[1.,1.],[v/(u+v)**2,-u/(u+v)**2]])
result={'one_observable_rank':int(np.linalg.matrix_rank(J1)),
        'with_equilibrium_rank':int(np.linalg.matrix_rank(J2)),
        'slow_schedule_max_h':4*math.log(2)/slow,'fast_schedule_max_h':4*math.log(2)/fast,
        'new_kinetic_fit':'NOT_RUN'}
if __name__=='__main__':print(json.dumps(result,indent=2))
