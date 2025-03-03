## installation

git clone https://github.com/champignon69/GEMAUT-pipeline.git

cd GEMAUT-pipeline

conda env create -n gemaut_env -f  gemaut_env.yml

conda activate gemaut_env

bash bash_install_saga_gemaut.bash

source $CONDA_PREFIX/etc/conda/activate.d/activate_gemaut.sh

script_gemaut --help
