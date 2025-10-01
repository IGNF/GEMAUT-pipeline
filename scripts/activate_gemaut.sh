

#!/bin/bash

# Définition des chemins d'installation (dans l'environnement conda)
export SAGA_INSTALL_DIR=${SAGA_INSTALL_DIR:-$CONDA_PREFIX}
export GEMAUT_INSTALL_DIR=${GEMAUT_INSTALL_DIR:-$CONDA_PREFIX}

# Détection automatique du bon répertoire de bibliothèques
if [ -d "$SAGA_INSTALL_DIR/lib64" ]; then
    SAGA_LIB_DIR="$SAGA_INSTALL_DIR/lib64"
elif [ -d "$SAGA_INSTALL_DIR/lib" ]; then
    SAGA_LIB_DIR="$SAGA_INSTALL_DIR/lib"
else
    echo "[WARNING] Aucun répertoire lib ou lib64 trouvé dans $SAGA_INSTALL_DIR"
fi

# Mettre à jour LD_LIBRARY_PATH dynamiquement à CHAQUE activation
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib:$SAGA_LIB_DIR

# Proj data
export PROJ_LIB=$CONDA_PREFIX/share/proj

# Les binaires sont déjà dans $CONDA_PREFIX/bin, pas besoin de modifier PATH
# (SAGA et GEMO sont installés directement dans l'environnement conda)

echo "GEMAUT and SAGA environment activated."


