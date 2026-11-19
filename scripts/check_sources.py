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
    process=json.loads((DATA/'atorvastatin_process_source.json').read_text(encoding='utf-8'))
    process_path=(DATA/process['file']).resolve();process_path.relative_to(DATA)
    require(sha(process_path)==process['sha256'],'Process source hash changed')
    process_xml=ET.parse(process_path)
    require(any(n.text==process['doi'] for n in process_xml.findall('.//article-id')),'Wrong process DOI')
    body=''.join(process_xml.getroot().itertext())
    require('96%' in body and '78%' in body,'Process yield anchors missing')
    caffeine=ET.parse(DATA/'source-responses/caffeine_kinetics.xml')
    require(any(n.text=='10.1186/s40064-015-0809-x' for n in caffeine.findall('.//article-id')),'Wrong caffeine DOI')
    caffeine_table=caffeine.find('.//table-wrap[@id="Tab4"]')
    expected_rates=[[float(''.join(c.itertext()).strip()) for c in row] for row in caffeine_table.findall('.//tr')[1:]]
    with (DATA/'caffeine_hydroxide_table4.csv').open(encoding='utf-8',newline='') as stream:
        reader=csv.reader(stream);next(reader);actual_rates=[[float(v) for v in row] for row in reader]
    require(len(expected_rates)==5 and expected_rates==actual_rates,'Caffeine CSV differs from primary Table 4')
    caffeine_card=json.loads((DATA/'caffeine_kinetics_provenance.json').read_text(encoding='utf-8'))
    require(sha(DATA/'source-responses/caffeine_kinetics.xml')==caffeine_card['sha256'],'Caffeine source hash changed')
    statin=ET.parse(DATA/'source-responses/statin_stability_verified.xml')
    require(any(n.text=='10.3390/pharmaceutics17070808' for n in statin.findall('.//article-id')),'Wrong statin stability DOI')
    target_folder=DATA/'target_qsar'
    target_manifest=json.loads((target_folder/'manifest.json').read_text(encoding='utf-8'))
    for name,digest in target_manifest['files_sha256'].items():
        target_path=(target_folder/name).resolve();target_path.relative_to(target_folder.resolve())
        require(sha(target_path)==digest,'Changed target QSAR artifact '+name)
    for prefix,target,endpoint in [('a2a','CHEMBL251','Ki'),('hmgcr','CHEMBL402','IC50')]:
        card=json.loads((target_folder/(prefix+'_dataset.json')).read_text(encoding='utf-8'))
        require(card['target']['target_chembl_id']==target and card['endpoint']==endpoint,'Wrong target/endpoint '+prefix)
        require(sha(target_folder/(prefix+'_curated.csv'))==card['sha256_curated_csv'],'Changed curated QSAR CSV '+prefix)
    print('PASS:',len(sources),'source hashes; 7 PubChem identities; 2 publication DOIs; 20 HPLC rows; 2 ChEMBL first pages')
    print('Scope: provenance/data consistency; no independent scientific review, assay or clinical validation')
    print('PASS: 5 caffeine kinetic rows match primary XML; caffeine and atorvastatin stability DOIs verified')
    print('PASS: frozen target-specific QSAR artifacts and target/endpoint identities verified')

if __name__=='__main__':main()
