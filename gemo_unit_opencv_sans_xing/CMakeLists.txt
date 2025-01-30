cmake_minimum_required(VERSION 3.5)  # Utilisez une version de CMake moderne si possible
project(main_GEMAUT_unit)

# Définir le type de build par défaut
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# OpenMP (activé par défaut dans GCC et Clang)
find_package(OpenMP REQUIRED)
if(OpenMP_CXX_FOUND)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
endif()

# OpenCV
find_package(OpenCV REQUIRED)
include_directories(${OpenCV_INCLUDE_DIRS})

# GSL
find_package(GSL REQUIRED)
include_directories(${GSL_INCLUDE_DIRS})

find_package(GDAL REQUIRED)
include_directories(${GDAL_INCLUDE_DIRS})

# Ajouter l'exécutable avec les fichiers sources
add_executable(main_GEMAUT_unit
    ../src/main_gemo_unit.cpp
    ../src/Normes.cpp
    ../src/Parametres.cpp
    ../src/GEA.cpp
    ../src/Attache_Donnees.cpp
    ../src/Terme_Regularisation.cpp
)

# Lier les bibliothèques nécessaires
target_link_libraries(main_GEMAUT_unit
    ${OpenCV_LIBS}
    ${GSL_LIBRARIES}
    ${GSL_CBLAS_LIBRARIES}
    ${GDAL_LIBRARIES}
    -lpthread           # Pour les threads
    -ldl                # Dynamic linker
)
