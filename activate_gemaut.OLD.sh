#!/bin/bash

# Définition des chemins d'installation
export SAGA_INSTALL_DIR=${SAGA_INSTALL_DIR:-$HOME/GEMAUT/saga_install}
export GEMAUT_INSTALL_DIR=${GEMAUT_INSTALL_DIR:-$HOME/GEMAUT/GEMO}

# Configuration des bibliothèques (PRIORITÉ aux libs systèmes !)

# Détection automatique du bon répertoire de bibliothèques
if [ -d "$SAGA_INSTALL_DIR/lib64" ]; then
    SAGA_LIB_DIR="$SAGA_INSTALL_DIR/lib64"
elif [ -d "$SAGA_INSTALL_DIR/lib" ]; then
    SAGA_LIB_DIR="$SAGA_INSTALL_DIR/lib"
else
    echo "[ERROR] Aucun répertoire lib ou lib64 trouvé dans $SAGA_INSTALL_DIR"
    exit 1
fi

# Génère le script d'activation avec le bon chemin
cat > "$CONDA_PREFIX/etc/conda/activate.d/env_vars.sh" <<EOF
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib:$SAGA_LIB_DIR
EOF

# export LD_LIBRARY_PATH=$SAGA_LIB_DIR:\$CONDA_PREFIX/lib:\$LD_LIBRARY_PATH

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
