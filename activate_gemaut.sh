#!/bin/bash

# Définition des chemins d'installation
export SAGA_INSTALL_DIR=${SAGA_INSTALL_DIR:-$HOME/GEMAUT/saga_install}
export GEMAUT_INSTALL_DIR=${GEMAUT_INSTALL_DIR:-$HOME/GEMAUT/GEMO}

# Configuration des bibliothèques (PRIORITÉ aux libs systèmes !)
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$SAGA_INSTALL_DIR/lib64
export PROJ_LIB=$CONDA_PREFIX/share/proj

# Ajouter les binaires de SAGA et GEMAUT au PATH
export PATH=$SAGA_INSTALL_DIR/bin:$GEMAUT_INSTALL_DIR/bin:$PATH

# Ajouter script_gemaut.py dans le PATH via un lien symbolique
if [ ! -f "$CONDA_PREFIX/bin/script_gemaut" ]; then
    ln -sf $HOME/GEMAUT/script_gemaut $CONDA_PREFIX/bin/script_gemaut
fi

# Ajouter script_gemaut.py dans le PATH via un lien symbolique
if [ ! -f "$CONDA_PREFIX/bin/saga_cmd" ]; then
    ln -sf $HOME/GEMAUT/saga_install/bin/saga_cmd $CONDA_PREFIX/bin/saga_cmd
fi

echo "GEMAUT and SAGA environment activated."
