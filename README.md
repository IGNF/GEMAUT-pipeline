## installation

git clone https://gitlab.ign.fr/GEMAUT/GEMAUT-Pipeline.git

cd GEMAUT-Pipeline

conda env create -n gemaut_env -f  gemaut_env.yml

conda activate gemaut_env

bash bash_install_saga_gemaut.bash

script_gemaut --help
