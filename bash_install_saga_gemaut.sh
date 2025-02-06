
CURRENT_DIR=${PWD}

### Définir un chemin d'installation configurable
SAGA_INSTALL_DIR=${SAGA_INSTALL_DIR:-$HOME/GEMAUT/saga_install}

## Créer le répertoire d’installation si besoin (avec droits root si nécessaire)
mkdir -p $SAGA_INSTALL_DIR
##chown $USER:$USER $SAGA_INSTALL_DIR

git clone https://git.code.sf.net/p/saga-gis/code saga-gis-code

## cd
cd $CURRENT_DIR/saga-gis-code/saga-gis/

if [ -d "build" ]; then
    rm -r build
fi
mkdir build
cd build

## Configuration et compilation
cmake -DCMAKE_INSTALL_PREFIX=$SAGA_INSTALL_DIR ..
cmake --build . --config Release --parallel $(nproc)
make install

# Définir un chemin d'installation configurable
GEMAUT_INSTALL_DIR=${GEMAUT_INSTALL_DIR:-$HOME/GEMAUT/GEMO}
mkdir -p $GEMAUT_INSTALL_DIR

cd $CURRENT_DIR
cd GEMO

#git clone https://gitlab.ign.fr/GEMAUT/GEMAUT-Pipeline.git

if [ -d "build" ]; then
    rm -r build
fi
mkdir build
cd build

# Créer le répertoire d’installation
mkdir -p $GEMAUT_INSTALL_DIR
##sudo chown $USER:$USER $GEMAUT_INSTALL_DIR

# Déplacer dans le répertoire de compilation
cmake -DCMAKE_INSTALL_PREFIX=$GEMAUT_INSTALL_DIR ..
make
make install

cd $CURRENT_DIR

mkdir -p $CONDA_PREFIX/etc/conda/activate.d
mkdir -p $CONDA_PREFIX/etc/conda/deactivate.d

cp activate_gemaut.sh   $CONDA_PREFIX/etc/conda/activate.d/ ; 
cp deactivate_gemaut.sh $CONDA_PREFIX/etc/conda/deactivate.d/

# Créer un lien symbolique dans le dossier personnel
ln -sf $CURRENT_DIR/script_gemaut.py $HOME/GEMAUT/script_gemaut
chmod +x $HOME/GEMAUT/script_gemaut

# Recharger l'environnement Conda pour appliquer immédiatement les changements
source $CONDA_PREFIX/etc/conda/activate.d/activate_gemaut.sh
