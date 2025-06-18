#!/bin/bash

# Nettoyage des variables spécifiques à GEMAUT
unset SAGA_INSTALL_DIR
unset GEMAUT_INSTALL_DIR
unset PROJ_LIB

# Nettoyage PATH
export PATH=${PATH//"$HOME\/GEMAUT\/saga_install\/bin:"/}
export PATH=${PATH//"$HOME\/GEMAUT\/GEMO\/bin:"/}

# Nettoyage LD_LIBRARY_PATH
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH//"$HOME\/GEMAUT\/saga_install\/lib64:"/}
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH//":$HOME\/GEMAUT\/saga_install\/lib64"/}
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH//"$HOME\/GEMAUT\/saga_install\/lib:"/}
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH//":$HOME\/GEMAUT\/saga_install\/lib"/}

# Suppression des liens symboliques si présents
rm -f "$CONDA_PREFIX/bin/script_gemaut"
rm -f "$CONDA_PREFIX/bin/saga_cmd"

echo "GEMAUT and SAGA environment deactivated."

