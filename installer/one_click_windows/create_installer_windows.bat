DEL /F/Q/S build > NUL
DEL /F/Q/S dist > NUL
RMDIR /Q/S build
RMDIR /Q/S dist
call conda env remove -n alphapeptinstaller 
call conda create -n alphapeptinstaller python=3.8 pip=20.2 -y
call conda activate alphapeptinstaller
call pip install ../../.
call pip install -r ../../requirements.txt
call pip install numpy==1.19.3
call pip install pyinstaller
call pyinstaller ../alphapept.spec -y
call pyinstaller ../alphapeptw.spec -y
call conda deactivate
call copy dist\alphapeptw\alphapeptw.exe dist\alphapept\alphapeptw.exe
call copy dist\alphapeptw\alphapeptw.exe.manifest dist\alphapept\alphapeptw.exe.manifest
call "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" alphapept_innoinstaller.iss
