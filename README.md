## installation

git clone https://gitlab.ign.fr/GEMAUT/GEMAUT-Pipeline.git

cd GEMAUT-Pipeline

conda env create -n env_test_install -f  gemaut_env.yml

conda activate env_test_install

bash bash_install_saga_gemaut.bash

script_gemaut --help
