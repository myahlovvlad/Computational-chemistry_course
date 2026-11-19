"""Process-local lossless HDF5 compression restricted to one owned scratch tree.

No integral screening, rounding, basis or electronic-method changes. h5py's
original methods are restored on exit, including exceptional exits.
"""
from contextlib import contextmanager
from pathlib import Path
import os
import shutil


class ScratchSpaceError(RuntimeError):
    pass


@contextmanager
def compressed_scratch(directory, *, minimum_free_bytes, ledger, minimum_dataset_bytes=1024**2):
    import h5py
    import numpy as np
    root=Path(directory).resolve()
    create=h5py.Group.create_dataset;write=h5py.Dataset.__setitem__
    def ours(obj):
        return Path(os.fsdecode(obj.file.filename)).resolve().is_relative_to(root)
    def reserve():
        free=shutil.disk_usage(root).free
        if free<minimum_free_bytes:
            raise ScratchSpaceError(f'Scratch reserve reached: {free} free bytes < {minimum_free_bytes}')
    def create_dataset(self,name,shape=None,dtype=None,data=None,**kwargs):
        if ours(self):
            reserve()
            actual_shape=shape if shape is not None else np.shape(data)
            actual_dtype=np.dtype(dtype if dtype is not None else getattr(data,'dtype',float))
            size=int(np.prod(actual_shape))*actual_dtype.itemsize if actual_shape else 0
            if len(actual_shape)>=2 and size>=minimum_dataset_bytes and actual_dtype.kind in 'fciub' and not kwargs.get('compression'):
                kwargs.update(compression='gzip',compression_opts=1,shuffle=True,fletcher32=True)
                ledger.append({'file':str(self.file.filename),'dataset':str(name),'uncompressed_bytes':size,
                               'compression':'gzip level 1, shuffle, Fletcher32; lossless','dtype':str(actual_dtype)})
        return create(self,name,shape=shape,dtype=dtype,data=data,**kwargs)
    def setitem(self,args,value):
        if ours(self):reserve()
        return write(self,args,value)
    h5py.Group.create_dataset=create_dataset;h5py.Dataset.__setitem__=setitem
    try:yield
    finally:
        h5py.Group.create_dataset=create;h5py.Dataset.__setitem__=write
