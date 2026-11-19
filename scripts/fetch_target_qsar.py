"""Acquire complete target/endpoint pages and curate auditable target-specific QSAR inputs."""
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import time
from urllib.parse import urlencode,urljoin,urlsplit

import requests
from rdkit import Chem

BASE='https://www.ebi.ac.uk/chembl/api/data/'
TARGETS={'A2A':('CHEMBL251','Ki','adenosine'),'HMGCR':('CHEMBL402','IC50','reductase')}


def save(path,value):
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)


class Acquisition:
    def __init__(self,out):self.out=out;self.session=requests.Session();self.count=0;self.records=[]

    def get(self,url,*,optional=False):
        if urlsplit(url).scheme!='https' or urlsplit(url).hostname!='www.ebi.ac.uk':raise ValueError('Unexpected pagination origin')
        self.count+=1;folder=self.out/'raw';folder.mkdir(exist_ok=True)
        last=None
        for attempt in range(1,4):
            try:
                response=self.session.get(url,timeout=(20,120))
                raw=response.content
                path=folder/f'{self.count:04}-attempt-{attempt}.json';path.write_bytes(raw)
                record={'url':url,'utc':datetime.now(timezone.utc).isoformat(),'http_status':response.status_code,
                        'file':path.relative_to(self.out).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),
                        'attempt':attempt,'content_type':response.headers.get('content-type')}
                self.records.append(record)
                with (self.out/'acquisition.jsonl').open('a',encoding='utf-8') as log:log.write(json.dumps(record)+'\n')
                response.raise_for_status();return response.json()
            except (requests.RequestException,ValueError) as error:
                last=error
                if attempt<3:time.sleep(attempt)
        if optional:return {'status':'UNAVAILABLE','error':str(last)}
        raise RuntimeError('Source acquisition failed: '+url) from last

    def pages(self,resource,filters,key):
        url=BASE+resource+'.json?'+urlencode({**filters,'limit':1000});seen=set();rows=[];total=None
        while url:
            if url in seen:raise ValueError('Repeated next page')
            seen.add(url);page=self.get(url);meta=page['page_meta']
            if total is None:total=meta['total_count']
            elif total!=meta['total_count']:raise ValueError('Total changed during pagination; do not mix snapshots')
            rows+=page[key];print(resource,'received',len(rows),'/',total,flush=True)
            url=urljoin(BASE,meta['next']) if meta.get('next') else None
        if len(rows)!=total:raise ValueError('Incomplete source pages')
        return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--target',choices=TARGETS,required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    target_id,endpoint,name_check=TARGETS[args.target];acq=Acquisition(out)
    target=acq.get(BASE+'target/'+target_id+'.json')
    if target['organism']!='Homo sapiens' or name_check not in target['pref_name'].lower():raise ValueError('Wrong biological target')
    release=acq.get(BASE+'status.json',optional=True)
    assays=acq.pages('assay',{'target_chembl_id':target_id,'confidence_score':9,'assay_type':'B'},'assays')
    assay_map={r['assay_chembl_id']:r for r in assays}
    activities=acq.pages('activity',{'target_chembl_id':target_id,'standard_type':endpoint,'standard_units':'nM'},'activities')
    accepted=[];rejected=[]
    for r in activities:
        reason=None;assay=assay_map.get(r.get('assay_chembl_id'))
        if assay is None:reason='assay not direct single-protein binding/biochemical confidence 9'
        elif assay.get('variant_sequence_accession') or assay.get('variant_sequence_mutation'):reason='variant target'
        elif r.get('standard_relation')!='=':reason='censored endpoint'
        elif r.get('data_validity_comment'):reason='data validity flag'
        elif r.get('potential_duplicate'):reason='potential duplicate source record'
        elif not r.get('canonical_smiles'):reason='missing structure'
        else:
            try:
                value=float(r['standard_value'])
                if not math.isfinite(value) or value<=0:raise ValueError('value')
                mol=Chem.MolFromSmiles(r['canonical_smiles'])
                if mol is None or mol.GetNumAtoms()==0:raise ValueError('structure')
                if len(Chem.GetMolFrags(mol))!=1:raise ValueError('multicomponent representation: no silent salt stripping')
                y=-math.log10(value*1e-9)
                if r.get('pchembl_value') is not None and abs(y-float(r['pchembl_value']))>.025:raise ValueError('pChEMBL mismatch')
                accepted.append({'activity_id':r['activity_id'],'molecule_chembl_id':r['molecule_chembl_id'],
                    'smiles':Chem.MolToSmiles(mol,isomericSmiles=True),'endpoint':endpoint,'p_value':y,
                    'assay_id':r['assay_chembl_id'],'document_id':r['document_chembl_id'],
                    'document_year':r.get('document_year'),'standard_value_nM':value})
            except (ValueError,TypeError,KeyError) as error:reason=str(error)
        if reason:rejected.append({'activity_id':r.get('activity_id'),'reason':reason,'record':r})
    by_structure={}
    for r in accepted:by_structure.setdefault(r['smiles'],[]).append(r)
    compounds=[]
    for smiles,rows in by_structure.items():
        values=[r['p_value'] for r in rows];spread=max(values)-min(values)
        if spread>1.0:
            rejected.append({'reason':'cross-assay spread >1 log unit; no uncritical median','smiles':smiles,'records':rows});continue
        compounds.append({'row_id':len(compounds),'smiles':smiles,'endpoint':'p'+endpoint,
           'y':statistics.median(values),'replicate_n':len(rows),'p_value_range':spread,
           'activity_ids':';'.join(str(r['activity_id']) for r in rows),
           'molecule_ids':';'.join(sorted({r['molecule_chembl_id'] for r in rows})),
           'assay_ids':';'.join(sorted({r['assay_id'] for r in rows})),
           'document_ids':';'.join(sorted({r['document_id'] for r in rows if r['document_id']}))})
    if not compounds:raise RuntimeError('No eligible target-specific compounds; do not substitute another target')
    with (out/'curated.csv').open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(compounds[0]));writer.writeheader();writer.writerows(compounds)
    save(out/'accepted_measurements.json',accepted);save(out/'rejected.json',rejected)
    report={'status':'PASS','target':target,'endpoint':endpoint,'release':release,'source_records':len(activities),
       'eligible_assays':len(assays),'accepted_measurements':len(accepted),'unique_curated_structures':len(compounds),
       'sha256_curated_csv':hashlib.sha256((out/'curated.csv').read_bytes()).hexdigest(),
       'licence':'ChEMBL / EMBL-EBI, CC BY-SA 3.0; retain source and share-alike attribution',
       'curation':'human target, confidence 9, type B, wild-type, exact relation, positive nM; no salt stripping; exact graph aggregation median only if spread <=1 log unit',
       'limitations':['Assay conditions are heterogeneous; pIC50 is not pKi','Missing assay conditions are not imputed as equivalent',
                      'This is a version-bound database snapshot, not new experimental measurement','Median aggregation does not eliminate inter-assay bias'],
       'model_training':'NOT_RUN','scientific_review':'NOT_RUN','acquisition':acq.records}
    save(out/'dataset.json',report);print(args.target,'curated structures',len(compounds),flush=True)


if __name__=='__main__':main()
