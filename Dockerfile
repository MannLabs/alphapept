FROM jupyter/base-notebook:python-3.8

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    apt-utils \
    build-essential \
    libgomp1 \
    gnupg \
    ca-certificates \
    && apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF \
    && echo "deb https://download.mono-project.com/repo/ubuntu stable-focal main" | sudo tee /etc/apt/sources.list.d/mono-official-stable.list \
    && apt update \
    && apt install -y mono-devel \
    && wget https://github.com/MannLabs/alphapept/blob/master/alphapept/ext/bruker/FF/linux64/libtbb.so.2 \
    && mv libtbb.so.2 /usr/lib/

RUN conda install -c anaconda pytables==3.6.1
RUN conda install -c conda-forge pythonnet
RUN conda install numba==0.55.2 numpy==1.20.3 pandas==1.4.3

COPY . .
RUN pip install ".[stable,gui-stable]"


CMD ["bash"]
