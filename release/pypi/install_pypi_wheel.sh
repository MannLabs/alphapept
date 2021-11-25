conda create -n alphapept_pip_test python=3.8 -y
conda activate alphapept_pip_test
pip install "alphapept[gui-stable]"
alphapept
conda deactivate
