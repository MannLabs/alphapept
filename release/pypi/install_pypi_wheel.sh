conda create -n alphapept_pip_test python=3.8 -y
conda activate alphapept_pip_test
pip install "alphapept[stable]"
alphapept
conda deactivate
