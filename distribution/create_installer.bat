cd %~dp0\..
python setup.py install
cd %~dp0
pyinstaller -y --hidden-import="sklearn.utils._cython_blas" --hidden-import="sklearn.neighbors.typedefs" --hidden-import="sklearn.neighbors.quad_tree" --hidden-import="sklearn.tree._utils" -n alphapept alphapept-script.py
pyinstaller -y --hidden-import="sklearn.utils._cython_blas" --hidden-import="sklearn.neighbors.typedefs" --hidden-import="sklearn.neighbors.quad_tree" --hidden-import="sklearn.tree._utils" --noconsole -n alphapeptw alphapept-script.py
copy dist\alphapeptw\alphapeptw.exe dist\alphapept\alphapeptw.exe
copy dist\alphapeptw\alphapeptw.exe.manifest dist\alphapept\alphapeptw.exe.manifest
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" alphapept.iss
