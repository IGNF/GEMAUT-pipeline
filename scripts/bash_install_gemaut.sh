# Définir un chemin d'installation configurable
GEMAUT_INSTALL_DIR=${GEMAUT_INSTALL_DIR:-$HOME/GEMAUT/gemaut}

cd ${PWD}

# Créer le répertoire d’installation
sudo mkdir -p $GEMAUT_INSTALL_DIR
sudo chown $USER:$USER $GEMAUT_INSTALL_DIR

# Déplacer dans le répertoire de compilation
cd build
cmake -DCMAKE_INSTALL_PREFIX=$GEMAUT_INSTALL_DIR ..
make
make install
