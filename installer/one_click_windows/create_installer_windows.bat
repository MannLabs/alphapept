call DEL /F/Q/S build > NUL
call DEL /F/Q/S dist > NUL
call RMDIR /Q/S build
call RMDIR /Q/S dist
IF EXIST C:\Users\admin\.conda\envs\alphapeptinstaller RMDIR /S /Q C:\Users\admin\.conda\envs\alphapeptinstaller
call conda env remove -n alphapeptinstaller
call conda create -n alphapeptinstaller python=3.8 -y
call conda activate alphapeptinstaller
call cd ../..
call DEL /F/Q/S build > NUL
call DEL /F/Q/S dist > NUL
call RMDIR /Q/S build
call RMDIR /Q/S dist
call python setup.py sdist bdist_wheel
call pip install dist/alphapept-0.5.0-py3-none-any.whl[stable,gui-stable,legacy-stable]
call pip install pyinstaller==4.10
call cd installer/one_click_windows
call pyinstaller ../alphapept.spec -y
call conda deactivate
call robocopy dist/alphapept/site-packages/st_aggrid dist/alphapept/st_aggrid /E
call "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" alphapept_innoinstaller.iss
