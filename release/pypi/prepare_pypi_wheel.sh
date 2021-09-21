cd ../..
conda create -n alphapept_pypi_wheel python=3.8
conda activate alphapept_pypi_wheel
pip install twine
rm -rf dist
rm -rf build
python setup.py sdist bdist_wheel
twine check dist/*
conda deactivate
