"""Проверить закреплённые байты и предметную идентичность источников; без сетевых запросов."""
from pathlib import Path
import csv,hashlib,json,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'practicuum/shared/data'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def require(condition,message):
    if not condition:raise ValueError(message)

def main():
    sources=json.loads((DATA/'sources-v2.json').read_text(encoding='utf-8'))
    for record in sources:
        path=(DATA/record['file']).resolve();path.relative_to(DATA)
        require(sha(path)==record['sha256'],'Изменились байты '+record['file'])
    for row in json.loads((DATA/'compounds.json').read_text(encoding='utf-8')):
        path=DATA/'source-responses'/('pubchem_'+row['name']+'.json')
        original=json.loads(path.read_text(encoding='utf-8'))['PropertyTable']['Properties'][0]
        require(sha(path)==row['source_sha256'],'Неверный raw SHA для '+row['name'])
        require(original['CID']==row['cid'] and original['SMILES']==row['smiles'],'Изменена идентичность '+row['name'])
        require(original['MolecularFormula']==row['formula'],'Изменена формула '+row['name'])
    for file,doi in [('hplc_article.xml','10.3390/molecules18032469'),
                     ('xanthine_synthesis_verified.xml','10.1186/1860-5397-2-20')]:
        doc=ET.parse(DATA/'source-responses'/file)
        require(any(node.text==doi for node in doc.findall('.//article-id')),'DOI не совпал '+file)
    hplc=ET.parse(DATA/'source-responses/hplc_article.xml')
    table=hplc.find(".//table-wrap[@id='molecules-18-02469-t001']")
    expected=[]
    for row in table.findall('.//tr'):
        cells=[''.join(node.itertext()).strip().replace('\u2212','-') for node in row if node.tag in ['td','th']]
        try:float(cells[0])
        except (ValueError,IndexError):continue
        expected.append([float(value) for value in cells])
    with (DATA/'atorvastatin_hplc_table1.csv').open(encoding='utf-8',newline='') as stream:
        reader=csv.reader(stream);next(reader);actual=[[float(v) for v in row] for row in reader]
    require(len(expected)==20 and expected==actual,'CSV не совпал с опубликованными 20 опытами')
    for name,cid in [('istradefylline','CHEMBL431770'),('atorvastatin','CHEMBL1487')]:
        source=json.loads((DATA/'source-responses'/(name+'_chembl_activities.json')).read_text(encoding='utf-8'))
        rows=source['activities']
        require(len(rows)==100 and all(r['molecule_chembl_id']==cid for r in rows),'Неверный объект ChEMBL')
    print('PASS:',len(sources),'source hashes; 7 PubChem identities; 2 publication DOIs; 20 HPLC rows; 2 ChEMBL first pages')
    print('Scope: provenance/data consistency; no independent scientific review, assay or clinical validation')

if __name__=='__main__':main()
