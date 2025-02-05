## Installation 

# Step 1: Clone the GEMAUT repo
git clone XXX 

# Step 2: Move in the GEMAUT folder
cd GEMAUT

# Step 3: Clone the SAGA repo
git clone https://git.code.sf.net/p/saga-gis/code saga-gis-code

# Step 4: conda create
conda create --name saga_env_local

# Step 5: conda activate
conda activate saga_env_local

# Step 6: conda install
conda install -c conda-forge pdal gcc_linux-64 gxx_linux-64 cmake make wxwidgets proj rasterio scipy tqdm gdal loguru

# Step 7: Move to the SAGA folder
cd saga-gis-code/saga-gis

### instal saga 

# Step 8: Create the build folder and move to it
mkdir build; cd build

# Step 9: 
cmake -DCMAKE_INSTALL_PREFIX=$HOME/saga_install ..

# Step 10: 
cmake --build . --config Release --parallel 12

# Step 11: 
make install

### instal GEMAUT

#cd ..
cd ..

#mkdir build
cd build

#config
cmake ..

#make
make

# configure your environment
echo 'export LD_LIBRARY_PATH=$HOME/saga_install/lib:/home/NChampion/anaconda3/envs/saga_env_local/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
echo 'export PROJ_LIB=/home/NChampion/anaconda3/envs/saga_env_local/share/proj' >> ~/.bashrc
echo 'export PATH=/home/NChampion/saga_install/bin:$PATH' >> ~/.bashrc
echo 'export PATH=$PATH:/home/NChampion/DATADRIVE1/DEVELOPPEMENT/GEMAUT-Pipeline/gemo_unit_opencv_sans_xing/build' >> ~/.bashrc

# 
source ~/.bashrc

# go to the GEMAUT folder and run it script
./script_gemaut.py --help 

############################################################################################################################################
### du coup, saga_cmd est installé ici >>> /home/NChampion/saga_install/bin/saga_cmd
### mais en lançant saga_cmd dans le terminal, saga s exécute ! 

mamba install -c conda-forge rasterio scipy tqdm gdal loguru

