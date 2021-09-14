FROM python:3.8.3

# Mono: 5.20

RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF \
  && echo "deb http://download.mono-project.com/repo/debian stretch/snapshots/5.20 main" > /etc/apt/sources.list.d/mono-official.list \
  && apt-get update \
  && apt-get install -y clang \
  && apt-get install -y mono-devel=5.20\* \
  && rm -rf /var/lib/apt/lists/* /tmp/*

# Pythonnet: 2.5.0 (from PyPI)
# Note: pycparser must be installed before pythonnet can be built

RUN pip install pycparser \
  && pip install pythonnet==2.5.0

WORKDIR /home/alphapept/
COPY . .

RUN pip install -r requirements.txt
RUN pip install .

CMD ["bash"]
