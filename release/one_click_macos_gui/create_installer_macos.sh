#!bash

# Initial cleanup
rm -rf dist
rm -rf build
FILE=alphapept.pkg
if test -f "$FILE"; then
  rm alphapept.pkg
fi
cd ../..
rm -rf dist
rm -rf build

# Creating a conda environment
conda create -n alphapeptinstaller python=3.8 -y
conda activate alphapeptinstaller

# Creating the wheel
python setup.py sdist bdist_wheel

# Setting up the local package
cd release/one_click_macos_gui
pip install "../../dist/alphapept-0.3.33-py3-none-any.whl[stable,gui-stable]"

# Creating the stand-alone pyinstaller folder
pip install pyinstaller==4.2
pyinstaller ../pyinstaller/alphapept.spec -y
conda deactivate

# If needed, include additional source such as e.g.:
# cp ../../alphapept/data/*.fasta dist/alphapept/data

# Wrapping the pyinstaller folder in a .pkg package
mkdir -p dist/alphapept/Contents/Resources
cp ../logos/alpha_logo.icns dist/alphapept/Contents/Resources
mv dist/alphapept_gui dist/alphapept/Contents/MacOS
cp Info.plist dist/alphapept/Contents
cp alphapept_terminal dist/alphapept/Contents/MacOS
cp ../../LICENSE.txt Resources/LICENSE.txt
cp ../logos/alpha_logo.png Resources/alpha_logo.png
chmod 777 scripts/*

pkgbuild --root dist/alphapept --identifier de.mpg.biochem.alphapept.app --version 0.3.33 --install-location /Applications/alphapept.app --scripts scripts alphapept.pkg
productbuild --distribution distribution.xml --resources Resources --package-path alphapept.pkg dist/alphapept_gui_installer_macos.pkg
