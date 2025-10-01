

#!/bin/bash

# Définition des chemins d'installation
export SAGA_INSTALL_DIR=${SAGA_INSTALL_DIR:-$HOME/GEMAUT/saga_install}
export GEMAUT_INSTALL_DIR=${GEMAUT_INSTALL_DIR:-$HOME/GEMAUT/GEMO}

# Détection automatique du bon répertoire de bibliothèques
if [ -d "$SAGA_INSTALL_DIR/lib64" ]; then
    SAGA_LIB_DIR="$SAGA_INSTALL_DIR/lib64"
elif [ -d "$SAGA_INSTALL_DIR/lib" ]; then
    SAGA_LIB_DIR="$SAGA_INSTALL_DIR/lib"
else
    echo "[ERROR] Aucun répertoire lib ou lib64 trouvé dans $SAGA_INSTALL_DIR"
    exit 1
fi

# Mettre à jour LD_LIBRARY_PATH dynamiquement à CHAQUE activation
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib:$SAGA_LIB_DIR

# Proj data
export PROJ_LIB=$CONDA_PREFIX/share/proj

# Ajouter les binaires au PATH
export PATH=$SAGA_INSTALL_DIR/bin:$GEMAUT_INSTALL_DIR/bin:$PATH

echo "GEMAUT and SAGA environment activated."


