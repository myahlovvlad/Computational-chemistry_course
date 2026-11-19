"""Extract three numerical facts from primary MoleculeNet BioC tables.

Full text is never exported with the course. Use --input for a personal local
BioC cache or fetch the public primary API; output always uses a new file.
"""
from datetime import datetime,timezone
import argparse,hashlib,json
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET
URL='https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC5868307/unicode'


def extract(payload):
    document=ET.fromstring(payload)
    dois={n.text.casefold() for n in document.findall('.//infon[@key="article-id_doi"]') if n.text}
    if '10.1039/c7sc02664a' not in dois:raise ValueError('Wrong source DOI')
    tables={}
    for passage in document.findall('.//passage'):
        info={n.get('key'):n.text for n in passage.findall('infon')}
        if info.get('type')=='table' and info.get('id')=='tab3':tables['tab3']=ET.fromstring(info['xml'])
    if 'tab3' not in tables:raise ValueError('Primary Table 3 is missing')
    rows=[]
    for tr in tables['tab3'].findall('.//tr'):
        cells=[' '.join(''.join(c.itertext()).split()) for c in tr]
        if len(cells)<4:continue
        name,metric,classic,graph=cells[-4:]
        if name not in {'ESOL','PDBbind (full)','BBBP'}:continue
        if metric not in {'RMSE','AUC-ROC'}:raise ValueError('Unsupported source metric')
        cm,cv=classic.rsplit(':',1);gm,gv=graph.rsplit(':',1)
        rows.append({'dataset':name,'metric':metric,'higher_is_better':metric=='AUC-ROC',
          'conventional_model':cm.strip(),'conventional_value':float(cv),'graph_model':gm.strip(),'graph_value':float(gv),
          'source_table':'Table 3 / tab3','uncertainty':'not supplied in this selected summary row; inspect full methods/results',
          'target_unit':'dimensionless' if metric=='AUC-ROC' else 'inspect dataset target definition; not stated in Table 3'})
    if len(rows)!=3 or {r['dataset'] for r in rows}!={'ESOL','PDBbind (full)','BBBP'}:
        raise ValueError('Selected primary rows incomplete or duplicated')
    return rows,document.findtext('.//document/infon[@key="license"]')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path)
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--compare',type=Path)
    args=parser.parse_args()
    if args.out.exists():raise FileExistsError('Choose a new output file')
    if args.input:payload=args.input.read_bytes();mode='provided local cache; no new HTTP request'
    else:
        with urllib.request.urlopen(URL,timeout=45) as response:payload=response.read()
        mode='public primary BioC API'
    rows,license_label=extract(payload)
    if args.compare:
        expected=json.loads(args.compare.read_text(encoding='utf-8'))
        if rows!=expected['rows'] or hashlib.sha256(payload).hexdigest()!=expected['source_cache_sha256']:
            raise ValueError('Primary-source facts or response bytes differ from the declared snapshot')
    result={'doi':'10.1039/C7SC02664A','source_url':URL,'source_cache_sha256':hashlib.sha256(payload).hexdigest(),
        'source_license_label':license_label,'acquisition_mode':mode,'utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Three selected factual rows, not full text or a complete table; source rights unchanged','rows':rows}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print('PASS primary DOI/Table 3 and',len(rows),'selected rows; full text not redistributed')


if __name__=='__main__':main()
