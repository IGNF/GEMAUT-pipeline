#!/bin/bash

# Définition des chemins d'installation
export SAGA_INSTALL_DIR=${SAGA_INSTALL_DIR:-$HOME/GEMAUT/saga_install}
export GEMAUT_INSTALL_DIR=${GEMAUT_INSTALL_DIR:-$HOME/GEMAUT/GEMO}

# Configuration des bibliothèques
export LD_LIBRARY_PATH=$SAGA_INSTALL_DIR/lib:$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
export PROJ_LIB=$CONDA_PREFIX/share/proj

# Ajouter les binaires de SAGA et GEMAUT au PATH
export PATH=$SAGA_INSTALL_DIR/bin:$GEMAUT_INSTALL_DIR/bin:$PATH

# Ajouter script_gemaut.py dans le PATH via un lien symbolique
if [ ! -f "$CONDA_PREFIX/bin/script_gemaut" ]; then
    ln -sf $HOME/GEMAUT/script_gemaut $CONDA_PREFIX/bin/script_gemaut
fi

# Ajouter script_gemaut.py dans le PATH via un lien symbolique
#if [ ! -f "$CONDA_PREFIX/bin/script_gemaut" ]; then
#    ln -sf $GEMAUT_INSTALL_DIR/script_gemaut.py $CONDA_PREFIX/bin/script_gemaut
#fi

echo "GEMAUT and SAGA environment activated."

