<p align="center">
  <img src="assets/logo.png" alt="GEMAUT" width="200" style="margin-right: 20px;"/>
  <img src="assets/Linux.png" alt="Linux" width="200"/>
</p>

L'outil pour le passage MNS > MNT sous Linux (& conda)

## installation

git clone https://github.com/IGNF/GEMAUT-pipeline.git

cd GEMAUT-pipeline

conda env create -n gemaut_env -f  gemaut_env.yml

conda activate gemaut_env

bash bash_install_saga_gemaut.bash

source $CONDA_PREFIX/etc/conda/activate.d/activate_gemaut.sh

script_gemaut --help

script_gemaut --mns /chem/vers/MNS_in.tif --out /chem/vers/MNT.tif --reso 4 --cpu 24 --RepTra /chem/vers/RepTra [--nodata_ext -32768] [--nodata_int -32767]
