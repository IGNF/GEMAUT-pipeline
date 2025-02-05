#!/bin/bash

# Suppression des variables d'environnement
unset LD_LIBRARY_PATH
unset PROJ_LIB

# Suppression propre des chemins ajoutés au PATH
if [[ -n "$SAGA_INSTALL_DIR" ]]; then
    export PATH=${PATH//"$SAGA_INSTALL_DIR/bin:"/}
fi
if [[ -n "$GEMAUT_INSTALL_DIR" ]]; then
    export PATH=${PATH//":$GEMAUT_INSTALL_DIR/bin"/}
fi

echo "GEMAUT and SAGA environment deactivated."

