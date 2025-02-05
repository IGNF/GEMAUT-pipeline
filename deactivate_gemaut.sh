#!/bin/bash

# Suppression des variables d'environnement
unset SAGA_INSTALL_DIR
unset GEMAUT_INSTALL_DIR
unset LD_LIBRARY_PATH
unset PROJ_LIB

# Suppression propre des chemins ajoutés au PATH
if [[ -n "$SAGA_INSTALL_DIR" ]]; then
    export PATH=${PATH//"$SAGA_INSTALL_DIR/bin:"/}
fi
if [[ -n "$GEMAUT_INSTALL_DIR" ]]; then
    export PATH=${PATH//"$GEMAUT_INSTALL_DIR/bin:"/}
fi

# Suppression du lien symbolique de script_gemaut.py
rm -f $CONDA_PREFIX/bin/script_gemaut

echo "GEMAUT and SAGA environment deactivated."

