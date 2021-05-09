call DEL /F/Q/S build > NUL
call DEL /F/Q/S dist > NUL
call RMDIR /Q/S build
call RMDIR /Q/S dist
call conda env remove -n alphapeptinstaller
call conda create -n alphapeptinstaller python=3.8 -y
call conda activate alphapeptinstaller
call cd ../..
call DEL /F/Q/S build > NUL
call DEL /F/Q/S dist > NUL
call RMDIR /Q/S build
call RMDIR /Q/S dist
call python setup.py sdist bdist_wheel
call pip install dist/alphapept-0.3.21-py3-none-any.whl
call pip install pyinstaller==4.2
call cd installer/one_click_windows
call pyinstaller ../alphapept.spec -y
call conda deactivate
call "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" alphapept_innoinstaller.iss
