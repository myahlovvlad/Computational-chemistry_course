from pathlib import Path
import json,math,sys
import xml.etree.ElementTree as ET
import numpy as np
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'programm/course.json').is_file())
doc=ET.parse(ROOT/'practicuum/shared/data/source-responses/statin_stability_verified.xml')
rows=[[''.join(c.itertext()).strip() for c in r] for r in doc.findall('.//table-wrap[@id="pharmaceutics-17-00808-t001"]//tr')][2:]
slow=float(rows[0][7]);fast=float(rows[1][7])
result={'reported_rate_ratio_pH4_5':fast/slow,'lactone_loss_half_relaxation_h':math.log(2)/slow,'acid_formation_half_relaxation_h':math.log(2)/fast,'new_kinetic_fit':'NOT_RUN'}
if __name__=='__main__':print(json.dumps(result,indent=2))
