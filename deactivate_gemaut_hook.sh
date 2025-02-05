#!/bin/bash

unset LD_LIBRARY_PATH
unset PROJ_LIB
export PATH=$(echo $PATH | sed -e "s|$SAGA_INSTALL_DIR/bin:||g" -e "s|:$GEMAUT_INSTALL_DIR/bin||g")

echo "GEMAUT and SAGA environment deactivated."
