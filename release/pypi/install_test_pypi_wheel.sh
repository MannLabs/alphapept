conda create -n alphapept_pip_test python=3.8 -y
conda activate alphapept_pip_test
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple "alphapept[stable]"
alphapept
conda deactivate
