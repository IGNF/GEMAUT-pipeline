<img src="assets/logo.png" alt="GEMAUT Logo" width="200"/>

L'outil pour le passage MNS > MNT

## installation

git clone https://github.com/IGNF/GEMAUT-pipeline.git

cd GEMAUT-pipeline

conda env create -n gemaut_env -f  gemaut_env.yml

conda activate gemaut_env

bash bash_install_saga_gemaut.bash

source $CONDA_PREFIX/etc/conda/activate.d/activate_gemaut.sh

script_gemaut --help

script_gemaut  --mns chem_vers_MNS_IN.tif --out chemin_vers_MNT_OUT.tif --reso 4 --RepTra RepTraVerif --nodata_ext -32768 --nodata_int -32767 --cpu 6
