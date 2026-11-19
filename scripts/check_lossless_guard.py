"""Exercise low-space rejection, path isolation, bitwise IO and patch restoration."""
from pathlib import Path
import json,shutil,sys,tempfile
import h5py
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'practicuum/shared'))
from lossless_scratch import compressed_scratch,ScratchSpaceError
def main():
    (ROOT/'tmp').mkdir(exist_ok=True)
    original_create=h5py.Group.create_dataset;original_write=h5py.Dataset.__setitem__;ledger=[]
    with tempfile.TemporaryDirectory(dir=ROOT/'tmp',prefix='guard-check-') as temporary:
        root=Path(temporary);inside=root/'owned-scratch';inside.mkdir();outside=root/'separate-test-file.h5'
        array=np.arange(10000,dtype=np.float64).reshape(100,100)
        rejected=False
        try:
            with compressed_scratch(inside,minimum_free_bytes=shutil.disk_usage(root).free+1024**3,ledger=ledger):
                with h5py.File(outside,'w') as f:f['data']=array
                with h5py.File(inside/'blocked.h5','w') as f:f['data']=array
        except ScratchSpaceError:rejected=True
        if not rejected:raise RuntimeError('Low-space write was not rejected')
        if h5py.Group.create_dataset is not original_create or h5py.Dataset.__setitem__ is not original_write:
            raise RuntimeError('h5py API was not restored after exception')
        with h5py.File(outside,'r') as f:
            if f['data'].compression is not None or not np.array_equal(f['data'][...],array):raise ValueError('Path isolation failed')
        with compressed_scratch(inside,minimum_free_bytes=0,ledger=ledger,minimum_dataset_bytes=1):
            with h5py.File(inside/'roundtrip.h5','w') as f:f['data']=array
        with h5py.File(inside/'roundtrip.h5','r') as f:
            if f['data'].compression!='gzip' or not np.array_equal(f['data'][...],array):raise ValueError('Bitwise roundtrip failed')
        print(json.dumps({'status':'PASS','scope':__doc__,'low_space_rejected':rejected,'restored_after_exception':True,
              'outside_scratch_unchanged':True,'numeric_roundtrip_bitwise':True}))
if __name__=='__main__':main()
