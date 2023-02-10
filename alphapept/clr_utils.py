import clr
import os
import numpy as np

clr.AddReference('System')
# from System.Runtime.InteropServices import Marshal
# from System import IntPtr, Int64
# def DotNetArrayToNPArray(src):
#     '''
#     See https://github.com/mobiusklein/ms_deisotope/blob/90b817d4b5ae7823cfe4ad61c57119d62a6e3d9d/ms_deisotope/data_source/thermo_raw_net.py#L217
#     '''
#     if src is None:
#         return np.array([], dtype=np.float64)
#     dest = np.empty(len(src), dtype=np.float64)
#     Marshal.Copy(
#         src, 0,
#         IntPtr.__overloads__[Int64](dest.__array_interface__['data'][0]),
#         len(src))
#     return dest

from System.Runtime.InteropServices import GCHandle, GCHandleType
import ctypes
def DotNetArrayToNPArray(src):
    '''
    See https://mail.python.org/pipermail/pythondotnet/2014-May/001527.html
    '''
    if src is None:
        return np.array([], dtype=np.float64)
    src_hndl = GCHandle.Alloc(src, GCHandleType.Pinned)
    try:
        src_ptr = src_hndl.AddrOfPinnedObject().ToInt64()
        bufType = ctypes.c_double*len(src)
        cbuf = bufType.from_address(src_ptr)
        dest = np.frombuffer(cbuf, dtype=cbuf._type_).copy()
    finally:
        if src_hndl.IsAllocated: src_hndl.Free()
        return dest

ext_dir = os.path.join(
    os.path.dirname(__file__),
    'ext'
)
