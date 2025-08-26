#!/bin/bash

# Nettoyage des variables spécifiques à GEMAUT
unset SAGA_INSTALL_DIR
unset GEMAUT_INSTALL_DIR
unset PROJ_LIB

# Nettoyage PATH
export PATH=${PATH//"$HOME\/GEMAUT\/saga_install\/bin:"/}
export PATH=${PATH//"$HOME\/GEMAUT\/GEMO\/bin:"/}

# Nettoyage LD_LIBRARY_PATH
if [ -d "\$HOME/GEMAUT/saga_install/lib64" ]; then
    SAGA_LIB_DIR="\$HOME/GEMAUT/saga_install/lib64"
elif [ -d "\$HOME/GEMAUT/saga_install/lib" ]; then
    SAGA_LIB_DIR="\$HOME/GEMAUT/saga_install/lib"
fi

# Nettoyage de LD_LIBRARY_PATH
if [ -n "\$SAGA_LIB_DIR" ]; then
    export LD_LIBRARY_PATH=\${LD_LIBRARY_PATH//\$SAGA_LIB_DIR:/}
    export LD_LIBRARY_PATH=\${LD_LIBRARY_PATH//:\$SAGA_LIB_DIR/}
    export LD_LIBRARY_PATH=\${LD_LIBRARY_PATH//\$SAGA_LIB_DIR/}
fi

#############
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH//"$HOME\/GEMAUT\/saga_install\/lib:"/}
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH//":$HOME\/GEMAUT\/saga_install\/lib"/}

# Suppression des liens symboliques si présents
rm -f "$CONDA_PREFIX/bin/gemaut"
rm -f "$CONDA_PREFIX/bin/saga_cmd"

echo "GEMAUT and SAGA environment deactivated."

