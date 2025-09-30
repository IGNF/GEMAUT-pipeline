#!/bin/bash
set -e  # Arrêter le script si une commande échoue

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Fonctions de logging
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration par défaut
CURRENT_DIR=${PWD}
SAGA_INSTALL_DIR=${SAGA_INSTALL_DIR:-$HOME/GEMAUT/saga_install}
GEMAUT_INSTALL_DIR=${GEMAUT_INSTALL_DIR:-$HOME/GEMAUT/GEMO}
PARALLEL_JOBS=$(nproc)

check_dependencies() {
    local deps=("git" "cmake" "make")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "$dep n'est pas installé"
            exit 1
        fi
    done

    # Vérification du compilateur C++
    if command -v g++ &> /dev/null; then
        log_info "g++ trouvé"
    elif command -v x86_64-conda-linux-gnu-g++ &> /dev/null; then
        log_info "compilateur conda trouvé (x86_64-conda-linux-gnu-g++)"
    else
        log_error "Aucun compilateur C++ trouvé"
        exit 1
    fi
}

# Vérification de l'environnement conda
check_conda_env() {
    if [[ -z "${CONDA_PREFIX}" ]]; then
        log_error "Vous devez être dans un environnement conda"
        exit 1
    fi
}

# Sauvegarde des installations existantes
backup_existing_install() {
    local install_dir=$1
    if [ -d "$install_dir" ]; then
        local backup_dir="${install_dir}_backup_$(date +%Y%m%d_%H%M%S)"
        log_warning "Installation existante trouvée dans $install_dir"
        log_info "Création d'une sauvegarde dans $backup_dir"
        mv "$install_dir" "$backup_dir"
    fi
}

# Installation de SAGA-GIS
install_saga() {
    log_info "Installation de SAGA-GIS..."
    
    # Créer le répertoire d'installation
    mkdir -p "$SAGA_INSTALL_DIR"
    
    # Se placer dans le répertoire courant
    cd "$CURRENT_DIR"
    
    # Supprimer l'ancien clone si existant
    if [ -d "saga-gis-code" ]; then
        log_info "Suppression de l'ancien clone de SAGA-GIS..."
        rm -rf saga-gis-code
    fi
    
    # Cloner SAGA-GIS (version 7.9.0 qui est compatible avec wxWidgets 3.0)
    log_info "Clonage de SAGA-GIS..."
    if ! git clone https://git.code.sf.net/p/saga-gis/code saga-gis-code; then
        log_error "Échec du clonage de SAGA-GIS"
        exit 1
    fi
    
    # Vérifier que le clone a réussi
    if [ ! -d "saga-gis-code" ]; then
        log_error "Le répertoire saga-gis-code n'a pas été créé"
        exit 1
    fi
    
    # Compiler SAGA-GIS
    log_info "Compilation de SAGA-GIS..."
    if [ -d "saga-gis-code/saga-gis" ]; then
        cd saga-gis-code/saga-gis
    else
        log_error "Structure du dépôt SAGA-GIS inattendue"
        exit 1
    fi
    
    # Supprimer l'ancien build si existant
    if [ -d "build" ]; then 
        rm -rf build
    fi
    
    # Créer et entrer dans le répertoire build
    mkdir build && cd build
    
    # Configuration et compilation avec options spécifiques pour CentOS 7
    log_info "Configuration de SAGA-GIS..."
    if ! cmake -DCMAKE_BUILD_TYPE=Release \
               -DCMAKE_INSTALL_PREFIX="$SAGA_INSTALL_DIR" \
               -DWITH_GUI=OFF \
               -DWITH_PYTHON=ON \
               ..; then
        log_error "Échec de la configuration CMake"
        exit 1
    fi
    
    log_info "Compilation de SAGA-GIS..."
    if ! cmake --build . --config Release --parallel "$PARALLEL_JOBS"; then
        log_error "Échec de la compilation"
        exit 1
    fi
    
    log_info "Installation de SAGA-GIS..."
    if ! make install; then
        log_error "Échec de l'installation"
        exit 1
    fi
    
    # Retourner au répertoire initial
    cd "$CURRENT_DIR"
    log_info "Installation de SAGA-GIS terminée avec succès"
}

# Installation de GEMO
install_gemo() {
    log_info "Installation de GEMO..."
    
    mkdir -p "$GEMAUT_INSTALL_DIR"
    cd "$CURRENT_DIR/GEMO"
    
    if [ -d "build" ]; then rm -rf build; fi
    mkdir build && cd build
    
    cmake -DCMAKE_INSTALL_PREFIX="$GEMAUT_INSTALL_DIR" ..
    make
    make install
    
    cd "$CURRENT_DIR"
}

# Configuration de l'environnement conda
setup_conda_env() {
    log_info "Configuration de l'environnement conda..."
    
    # Créer les répertoires pour les scripts d'activation/désactivation
    mkdir -p "$CONDA_PREFIX/etc/conda/activate.d"
    mkdir -p "$CONDA_PREFIX/etc/conda/deactivate.d"
    
    # Copier les scripts
    cp activate_gemaut.sh "$CONDA_PREFIX/etc/conda/activate.d/"
    cp deactivate_gemaut.sh "$CONDA_PREFIX/etc/conda/deactivate.d/"
}

# Nettoyage
cleanup() {
    log_info "Nettoyage des fichiers temporaires..."
    if [ -d "saga-gis-code" ]; then rm -rf saga-gis-code; fi
    find . -name "build" -type d -exec rm -rf {} + 2>/dev/null || true
}

# Création du script de désinstallation
create_uninstall_script() {
    log_info "Création du script de désinstallation..."
    cat > uninstall_deps.sh << EOF
#!/bin/bash
rm -rf "$SAGA_INSTALL_DIR"
rm -rf "$GEMAUT_INSTALL_DIR"
rm -f "$CONDA_PREFIX/etc/conda/activate.d/activate_gemaut.sh"
rm -f "$CONDA_PREFIX/etc/conda/deactivate.d/deactivate_gemaut.sh"
EOF
    chmod +x uninstall_deps.sh
}

# Programme principal
main() {
    log_info "Début de l'installation des dépendances externes (SAGA + GEMO)..."
    
    # Vérifications initiales
    check_dependencies
    check_conda_env
    
    # Sauvegarder les installations existantes
    backup_existing_install "$SAGA_INSTALL_DIR"
    backup_existing_install "$GEMAUT_INSTALL_DIR"
    
    # Installation
    install_saga
    install_gemo
    setup_conda_env
    
    # Finalisation
    create_uninstall_script
    cleanup
    
    # Recharger l'environnement
    source "$CONDA_PREFIX/etc/conda/activate.d/activate_gemaut.sh"
    
    log_info "Installation des dépendances terminée avec succès!"

    log_info "Veuillez exécuter la commande suivante pour recharger l'environnement :"
    echo ""
    echo -e "${GREEN}    conda deactivate && conda activate $(basename "$CONDA_PREFIX")${NC}"
    echo ""
    log_info "Cette commande est ESSENTIELLE pour que GEMAUT fonctionne correctement !"
    echo ""
}

# Exécution du programme principal
main "$@"
