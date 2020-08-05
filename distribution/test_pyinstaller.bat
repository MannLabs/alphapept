DEL /F/Q/S build > NUL
DEL /F/Q/S dist > NUL
RMDIR /Q/S build
RMDIR /Q/S dist
cd %~dp0\..
python setup.py install
cd %~dp0
pyinstaller -y --hidden-import="sklearn.utils._cython_blas" --hidden-import="sklearn.neighbors.typedefs" --hidden-import="sklearn.neighbors.quad_tree" --hidden-import="sklearn.tree._utils" -n alphapept alphapept-script.py
dist\alphapept\alphapept.exe gui
