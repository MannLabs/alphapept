#!bash

# Initial cleanup
rm -rf dist
rm -rf build
cd ../..
rm -rf dist
rm -rf build

# Creating a conda environment
conda create -n alphapept_installer python=3.8 -y
conda activate alphapept_installer

# Creating the wheel
python setup.py sdist bdist_wheel

# Setting up the local package
cd release/one_click_windows_gui
# Make sure you include the required extra packages and always use the stable or very-stable options!
pip install "../../dist/alphapept-0.4.2-py3-none-any.whl[stable,gui-stable]"

# Creating the stand-alone pyinstaller folder
pip install pyinstaller==4.2
pyinstaller ../pyinstaller/alphapept.spec -y
conda deactivate

# If needed, include additional source such as e.g.:
# cp ../../alphapept/data/*.fasta dist/alphapept/data

# Wrapping the pyinstaller folder in a .exe package
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" alphapept_innoinstaller.iss
# WARNING: this assumes a static location for innosetup
