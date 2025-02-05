#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###
#****!/usr/local/bin/python3 
import rasterio
from rasterio.windows import Window
import subprocess
import numpy as np
from scipy.ndimage import generic_filter
import os, time, shutil, math
from tqdm import tqdm
import signal
import sys
from multiprocessing import Process,Pool,cpu_count
import argparse
from concurrent.futures import ProcessPoolExecutor
from osgeo import gdal, osr
gdal.UseExceptions()
from loguru import logger

# Fixer la variable d'environnement OMP_NUM_THREADS pour limiter les threads OpenMP
os.environ['OMP_NUM_THREADS'] = '1'

#chem_exe_saga="/home/nchampion/DEV/SAGA/saga-9.5.1/saga-gis/build/src/saga_core/saga_cmd/saga_cmd"
chem_exe_saga="saga_cmd"

#################################################################################################### 
def init_worker():
	signal.signal(signal.SIGINT, signal.SIG_IGN)

####################################################################################################
def contient_donnees(chem_mns, no_data_value=-9999):
    # Ouvrir l'image raster
    with rasterio.open(chem_mns) as src:
        # Lire les données du raster dans un tableau numpy
        data = src.read(1)  # Lecture de la première bande (ou unique bande)
        return not np.all(data == no_data_value)
    
# Fonction pour exécuter gdal_translate via subprocess
def run_task_sans_SORTIEMESSAGE(cmd):
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def run_task(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        return False
    return True

################################################################################################################################
def run_saga_par_dalle_parallel_avec_carte_pentes(RepIN,RepOUT,chem_pente_par_dallle,taille_dallage,rayon,no_data,iNbreCPU):

    liste_pixel_coords=[]
    liste_images=[]
    liste_rep_out=[]

    for root, dirs, files in os.walk(RepIN):
        for f in files:
            #
            liste_tmp=f.split('_')
            ligne_tmp=int(liste_tmp[1])
            colonne_tmp=int(liste_tmp[2].split('.')[0])
            # 
            ligne=(ligne_tmp-1)*taille_dallage
            colonne=(colonne_tmp-1)*taille_dallage
            #
            pixel_coords=[ligne,colonne]
            liste_pixel_coords.append(pixel_coords)
            #
            liste_images.append(os.path.join(root,f))

            # préparer / créer le dossier de sortie et l'ajouter à la liste
            chem_RepTra_SAGA_OUT_1_dalle=os.path.join(RepOUT,f[:-4])
            if not os.path.isdir(chem_RepTra_SAGA_OUT_1_dalle): os.mkdir(chem_RepTra_SAGA_OUT_1_dalle)
            liste_rep_out.append(chem_RepTra_SAGA_OUT_1_dalle)

    tasks = []

    # Ouverture de l'image une seule fois
    with rasterio.open(chem_pente_par_dallle) as dataset:
        band_data = dataset.read(1)
        #
        for (row, col), chem_img, chem_rep_out in zip(liste_pixel_coords, liste_images, liste_rep_out):
            #
            chem_ground=os.path.join(chem_rep_out,'ground.sdat')
            chem_ground_tif=os.path.join(chem_rep_out,'ground.tif')
            chem_non_ground=os.path.join(chem_rep_out,'non_ground.sdat')
            #
            if contient_donnees(chem_img, no_data):
                pente_local = band_data[row, col]
                # cmd_saga_1_dalle=f"{chem_exe_saga} grid_filter 7 -INPUT {chem_img} -RADIUS {rayon} -TERRAINSLOPE {pente_local} -GROUND {chem_ground} -NONGROUND {chem_non_ground} > /dev/null 2>&1 "
                cmd_saga_1_dalle=f"{chem_exe_saga} grid_filter 7 -INPUT {chem_img} -RADIUS {rayon} -TERRAINSLOPE 15 -GROUND {chem_ground} -NONGROUND {chem_non_ground} > /dev/null 2>&1 "
                logger.info(f"{cmd_saga_1_dalle}")
                tasks.append(cmd_saga_1_dalle)
                logger.info(f"cmd_saga_1_dalle {cmd_saga_1_dalle}")
            else:
                #on copie directement la dalle MNS no_data dans le ground.tif, ça sert juste pour l'assemblage plus tard [implémentation très sale]
                shutil.copyfile(chem_img, chem_ground_tif) 

    #run_task_sans_SORTIEMESSAGE
    with Pool(processes=iNbreCPU) as pool:
        list(tqdm(pool.imap_unordered(run_task_sans_SORTIEMESSAGE, tasks), total=len(tasks), desc="Lancement de SAGA unitaire en parallèle"))

    return


################################################################################################################################
def run_saga_par_dalle_parallel(RepIN,RepOUT,rayon,no_data,pente,iNbreCPU):

    tasks = []

    for root, dirs, files in os.walk(RepIN):
        for f in files:
            #
            # préparer / créer le dossier de sortie et l'ajouter à la liste
            chem_rep_out=os.path.join(RepOUT,f[:-4])
            if not os.path.isdir(chem_rep_out): os.mkdir(chem_rep_out)

            chem_img=os.path.join(root,f)
            chem_ground=os.path.join(chem_rep_out,'ground.sdat')
            chem_ground_tif=os.path.join(chem_rep_out,'ground.tif')
            chem_non_ground=os.path.join(chem_rep_out,'non_ground.sdat')
            #
            if contient_donnees(chem_img, no_data):
                # cmd_saga_1_dalle=f"{chem_exe_saga} grid_filter 7 -INPUT {chem_img} -RADIUS {rayon} -TERRAINSLOPE {pente_local} -GROUND {chem_ground} -NONGROUND {chem_non_ground} > /dev/null 2>&1 "
                cmd_saga_1_dalle=f"{chem_exe_saga} grid_filter 7 -INPUT {chem_img} -RADIUS {rayon} -TERRAINSLOPE {pente} -GROUND {chem_ground} -NONGROUND {chem_non_ground} > /dev/null 2>&1 "
                logger.info(f"{cmd_saga_1_dalle}")
                tasks.append(cmd_saga_1_dalle)
                logger.info(f"cmd_saga_1_dalle {cmd_saga_1_dalle}")
            else:
                #on copie directement la dalle MNS no_data dans le ground.tif, ça sert juste pour l'assemblage plus tard [implémentation très sale]
                shutil.copyfile(chem_img, chem_ground_tif) 

    #run_task_sans_SORTIEMESSAGE
    with Pool(processes=iNbreCPU) as pool:
        list(tqdm(pool.imap_unordered(run_task_sans_SORTIEMESSAGE, tasks), total=len(tasks), desc="Lancement de SAGA unitaire en parallèle"))

    return
            
############################################################################################################
def Daller_pente(chem_pente_filtree,chem_pente_par_dallle,taille_carre):
    #
    pente_data = rasterio.open(chem_pente_filtree)
    pente_array = pente_data.read(1)

    # Créer une matrice pour stocker les résultats
    result_pente_par_dalle = np.zeros_like(pente_array)

    # Parcourir l'image de pente par carrés de tailleXtaille pixels
    for i in range(0, pente_array.shape[0], taille_carre):
        for j in range(0, pente_array.shape[1], taille_carre):
            # Calcul des indices de fin, en s'assurant qu'ils ne dépassent pas les dimensions de l'image
            i_end = min(i + taille_carre, pente_array.shape[0])
            j_end = min(j + taille_carre, pente_array.shape[1])

            # Extraire un carré de 50x50 pixels ou moins si en bordure
            carre = pente_array[i:i_end, j:j_end]

            if carre.size == 0:
                continue

            # Calculer la pente max
            pente_max = np.max(carre)
            # autres possibilités
            # pente_mediane = np.median(carre)
            # quintile_percent = 80
            # pente_quintile = np.percentile(carre, quintile_percent)

            # ecrire
            result_pente_par_dalle[i:i_end, j:j_end] = pente_max

    #
    with rasterio.open(
        chem_pente_par_dallle,
        'w',
        driver='GTiff',
        height=result_pente_par_dalle.shape[0],
        width=result_pente_par_dalle.shape[1],
        count=1,
        dtype=result_pente_par_dalle.dtype,
        crs=pente_data.crs,
        transform=pente_data.transform
    ) as dst:
        dst.write(result_pente_par_dalle, 1)

    return

############################################################################################################
def Calculer_pente_filtree(chem_mns, RepTra_tmp, chem_pente_filtree, percentile=5, taille=5, seuil_diff=15):
    #
    chem_pente=os.path.join(RepTra_tmp,'pente.tif')
    chem_pente_smooth=os.path.join(RepTra_tmp,'pente_smooth.tif')
    #
    generate_slope_raster(chem_mns, chem_pente)
    #
    calculer_pente_smooth_percentile_fenetre(chem_pente, chem_pente_smooth, percentile, taille)
    #
    filtrer_pente(chem_pente, chem_pente_smooth, seuil_diff, chem_pente_filtree)

############################################################################################################
def generate_slope_raster(chem_mns, chem_pente):

    # NON VALIDE en EPSG:4326 quand l'Unité des Z diff Unité de XY
    # cmd = "gdaldem slope -alg ZevenbergenThorne {} {}".format(chem_mns, chem_pente)
    # os.system(cmd)
    """
    Generates a slope raster from a DSM using gdaldem slope.
    
    Parameters:
        chem_mns (str): Path to the DSM file.
        chem_pente (str): Path to output slope raster.
    """
    # Open the DSM file
    ds = gdal.Open(chem_mns)
    if ds is None:
        raise FileNotFoundError(f"Cannot open DSM file: {chem_mns}")

    # Get the projection information
    proj = ds.GetProjection()
    spatial_ref = osr.SpatialReference(wkt=proj)
    
    # Check if the projection is geographic (lat/lon) or projected (meters)
    if spatial_ref.IsGeographic():
        # Extract latitude of the center of the DSM
        transform = ds.GetGeoTransform()
        center_y = transform[3] + (transform[5] * ds.RasterYSize / 2)
        
        # Calculate scale factor based on the center latitude
        scale_factor = (111320 + (111320 * math.cos(math.radians(center_y)))) / 2

        # Run gdaldem slope with scale parameter
        cmd = [
            "gdaldem", "slope", "-alg", "ZevenbergenThorne",
            "-scale", str(scale_factor),
            chem_mns, chem_pente
        ]
        logger.info(f"Running gdaldem command with scale factor: {' '.join(cmd)}")
    else:
        # For projected coordinate systems, no scale parameter is needed
        cmd = [
            "gdaldem", "slope", "-alg", "ZevenbergenThorne",
            chem_mns, chem_pente
        ]
        logger.info(f"Running gdaldem command without scale factor: {' '.join(cmd)}")
    
    # Execute the command
    subprocess.run(cmd, check=True)

    # Close the dataset
    ds = None

############################################################################################################
# Fonction de calcul du percentile, définie en dehors de la fonction principale
def get_percentile_fenetre(values, percentile=5):
    """Calcule le percentile spécifié en ignorant les valeurs NaN."""
    return np.percentile(values[~np.isnan(values)], percentile) if np.any(~np.isnan(values)) else np.nan

############################################################################################################
def calculer_pente_smooth_percentile_fenetre(chem_pente, chem_pente_smooth, percentile=5, taille_fenetre=5):
    with rasterio.open(chem_pente) as src:
        # Lire la bande de données
        data = src.read(1)
        
        # Appliquer le filtre générique avec la fonction définie séparément
        resultat = generic_filter(data, lambda x: get_percentile_fenetre(x, percentile), size=(taille_fenetre, taille_fenetre), mode='constant', cval=np.nan)
        
        # Mettre à jour le profil pour la sortie
        profile = src.profile
        profile.update(dtype=rasterio.float32, count=1, compress='lzw')
        
        # Écrire le résultat dans un nouveau fichier raster
        with rasterio.open(chem_pente_smooth, 'w', **profile) as dst:
            dst.write(resultat, 1)

############################################################################################################
def filtrer_pente(chem_pente, chem_pente_smooth, seuil_diff, chem_pente_filtree):
    # Ouverture des deux rasters
    with rasterio.open(chem_pente) as src1, rasterio.open(chem_pente_smooth) as src2:
        # Vérifier que les dimensions et la transformation géospatiale sont identiques
        if not (src1.width == src2.width and src1.height == src2.height and src1.transform == src2.transform):
            raise ValueError("Les rasters doivent avoir la même taille et la même transformation géospatiale.")
        
        # Lecture des données des rasters sous forme de matrices numpy
        data1 = src1.read(1)  # chem_pente
        data2 = src2.read(1)  # chem_pente_smooth
        #
        # Calcul de la différence
        diff = data1 - data2 
        
        # Création du résultat basé sur la différence par rapport au seuil
        result = np.where(diff > seuil_diff, data2, data1)
        
        # Création des méta-données pour le fichier de sortie
        out_meta = src1.meta.copy()
        out_meta.update({
            'dtype': 'float32',  # Modifier le type de données si nécessaire
            'nodata': None
        })
        
        # Écriture du raster de sortie
        with rasterio.open(chem_pente_filtree, 'w', **out_meta) as dest:
            dest.write(result.astype('float32'), 1)

################################################################################################################################
def Decouper_image_en_dalles(chem_mns, taille_dallage, RepTra_DALLAGE_tmp, nom_generic='DALLAGE_'):
    # Charger l'image en entrée
    with rasterio.open(chem_mns) as src:
        largeur = src.width
        hauteur = src.height
        profile = src.profile
        
        # Créer le répertoire de sortie s'il n'existe pas
        if not os.path.exists(RepTra_DALLAGE_tmp):
            os.makedirs(RepTra_DALLAGE_tmp)
        
        # Calculer le nombre de dalles en fonction de la taille spécifiée
        nombre_lignes = (hauteur + taille_dallage - 1) // taille_dallage
        nombre_colonnes = (largeur + taille_dallage - 1) // taille_dallage
        total_dalles = nombre_lignes * nombre_colonnes  # Total des dalles à traiter
        
        with tqdm(total=total_dalles, desc="Découpage en dalles", unit="dalle") as pbar:
            # Boucler sur chaque dalle
            for i in range(nombre_lignes):
                for j in range(nombre_colonnes):
                    # Calculer les coordonnées de la fenêtre pour la dalle
                    x_offset = j * taille_dallage
                    y_offset = i * taille_dallage
                    width = min(taille_dallage, largeur - x_offset)
                    height = min(taille_dallage, hauteur - y_offset)
                
                    # Définir la fenêtre de découpe
                    window = Window(x_offset, y_offset, width, height)
                    transform_window = src.window_transform(window)
                
                    # Mettre à jour le profil pour correspondre à la taille de la dalle
                    profile.update({
                        'height': height,
                        'width': width,
                        'transform': transform_window
                    })
                
                    # Nommer et enregistrer la dalle
                    nom_dalle = f"DALLAGE_{i + 1}_{j + 1}.tif"
                    nom_dalle = f"{nom_generic}{i + 1}_{j + 1}.tif"
                    chemin_dalle = os.path.join(RepTra_DALLAGE_tmp, nom_dalle)
                
                    with rasterio.open(chemin_dalle, 'w', **profile) as dst:
                        dst.write(src.read(window=window))

                    pbar.update(1)
                
################################################################################################################################
def Creer_image_binaire(chem_out_final_expand_tmp, chem_out_final_expand, no_data_ext):
    # Ouvrir l'image en mode lecture
    logger.info(f"[SAGA] Creer_image_binaire de : {chem_out_final_expand_tmp} en {chem_out_final_expand}")
    with rasterio.open(chem_out_final_expand_tmp) as src:
        # Lire les métadonnées et les données de l'image
        profile = src.profile
        data = src.read(1)  # Lire la première bande

        # Créer une image binaire où la valeur est 1 si le pixel vaut no_data_ext ou -99999, sinon 0
        binary_data = np.where((data == no_data_ext) | (data == -99999), 1, 0).astype(np.uint8)

        # Mettre à jour le profil pour un fichier de sortie binaire
        profile.update(
            dtype=rasterio.uint8,
            count=1,
            nodata=None,  # Pas de valeur nodata pour une image binaire
            compress='lzw'  # Compression pour réduire la taille du fichier (optionnel)
        )

        # Créer l'image de sortie codée sur 1 bit
        with rasterio.open(chem_out_final_expand, 'w', **profile) as dst:
            dst.write(binary_data, 1)

    logger.info(f"[SAGA] Creer_image_binaire OK")

        # Raboutage_DALLAGE_SAGA(RepTra_OUT_SAGA_tmp_expand,chem_out_final_expand_tmp,iNbreCPU)

        # tasks_gdal = []
        # for root, dirs, files in os.walk(RepTra_OUT_SAGA_tmp_expand):
        #     for f in files:
        #         if f.startswith('ground') and f.endswith('sdat'):
        #             chem_in = os.path.join(root, f)
        #             chem_out = f"{chem_in[:-5]}.tif"
        #             cmd = f"gdal_translate {chem_in} {chem_out}"
        #             tasks_gdal.append(cmd)
        #             logger.info(cmd)
                    
############################################################################################################
def Raboutage_DALLAGE_SAGA(RepTra_DALLAGE_SAGA_in,RepTra_raboutage_tmp,chem_out,iNbreCPU):
    #
    dirs_col=[]
    dirs_lig=[]
    #
    for root, dirs, files in os.walk(RepTra_DALLAGE_SAGA_in):
        for dir_name in dirs:
            if dir_name.startswith("DALLAGE"):
                dirs_col.append(int(dir_name.split('_')[1]))
                dirs_lig.append(int(dir_name.split('_')[2]))  
    #
    max_col = max(dirs_col)
    max_lig = max(dirs_lig)
    #
    logger.info(f"[RABOUTAGE PAR LIGNE] max_col : {max_col}")
    logger.info(f"[RABOUTAGE PAR LIGNE] max_lig : {max_lig}")
    tasks = []
    #
    for col in range(max_col):
        # 
        liste_files=[]
        #
        for lig in range(max_lig):

            #
            folder_number_col = f"{col+1}"
            folder_number_lig = f"{lig+1}"                
            folder_name=f"DALLAGE_{folder_number_col}_{folder_number_lig}"
            #
            logger.info(f"recherche dans >> {os.path.join(RepTra_DALLAGE_SAGA_in,folder_name)}")
            #
            for root, dirs, files in os.walk(os.path.join(RepTra_DALLAGE_SAGA_in,folder_name)):
                for file in files:
                    if file.startswith('ground') and file.endswith("tif"):
                        liste_files.append(os.path.join(root,file))

        #rajouter un dossier de travail     
        output_file = os.path.join(RepTra_raboutage_tmp,f"out_{col+1}.tif")  
        cmd = f"gdal_merge.py -n -99999 -a_nodata -99999  -o {output_file} {' '.join(liste_files)} "
        logger.info(f"[RABOUTAGE PAR LIGNE] : {cmd}")
        #cmd = f"gdal_merge.py -n -99999 -a_nodata -99999  -o {output_file} {' '.join(liste_files)} > /dev/null 2>&1 "
        tasks.append(cmd)

    # # Initialize the pool
    with Pool(processes=iNbreCPU, initializer=init_worker) as pool:
        # run_task_sans_SORTIEMESSAGE // run_task
        results = list(tqdm(pool.imap_unordered(run_task_sans_SORTIEMESSAGE, tasks), total=len(tasks), desc="RABOUTAGE des ground.tif par ligne / AVEC SORTIEMESSAGE "))
        #results = list(tqdm(pool.imap_unordered(run_task_sans_SORTIEMESSAGE, tasks), total=len(tasks), desc="RABOUTAGE des ground.tif par ligne / SANS SORTIEMESSAGE"))
        
    tif_files = ' '.join([os.path.join(RepTra_raboutage_tmp,f'out_{col+1}.tif') for col in range(max_col)])
    cmd = f"gdal_merge.py -n -99999 -a_nodata -99999  -o {chem_out} {tif_files} > /dev/null 2>&1 "
    logger.info(f"[RABOUTAGE FINAL] : {cmd}")
    os.system(cmd)
    
####################################################################################################
def parse_arguments():

    parser = argparse.ArgumentParser(description="extract ground points from DSM avec SAGA")

    # Création du parseur d'arguments avec une description et un épilogue pour l'exemple de commande
    parser = argparse.ArgumentParser(
        description='extract ground points from DSM with SAGA',
        epilog="""EXEMPLE DE LIGNE DE COMMANDE:
        [/usr/local/bin/python3] /Volumes/ALI_Serveur/OUTILS_IGNE/OUTILS_DIVERS/GEMAUT/SAGA/main_extract_ground_points_with_saga_dallage.py --mns MNS.tif --out MASQUE_GROUND_NON_GROUND_out.tif --RepTra RepTra [--radius 50] [--tile 50] [--cpu 24] [--nodata_ext 32767]
            
    """
    )        
        
    parser.add_argument("--mns", type=str, required=True, help="chemin vers le MNS")
    parser.add_argument("--out", type=str, required=True, help="output GROUND/NON-GROUND mask")
    parser.add_argument("--RepTra", type=str, required=True, help="repetoire de travail")
    parser.add_argument("--radius", type=int, required=True, help="rayon d'analyse pour SAGA")
    parser.add_argument("--tile", type=int, default=50, help="taille de la tuile")        
    parser.add_argument("--cpu", type=int, default=8, help="nombre de CPUs à utiliser dans le traitement")
    parser.add_argument("--nodata_ext", type=int, default=-32768, required=True, help="Valeur du no_data EXTERIEUR sur les bords de chantier")

    ### 
    return parser.parse_args(sys.argv[1:])

############################################################################################################
#def main_saga_ground_extraction_avec_carte_pentes(args):
def main_saga_ground_extraction_avec_carte_pentes(chem_mns, chem_out_final, RepTra, iNbreCPU, rayon, taille_dallage, no_data_ext, taille_voisinage=5, K=2, percentile=5, seuil_diff=15):
    
    try:

        logger.info("[SAGA] Démarrage de main_saga_ground_extraction")

        # Enregistrer l'heure de départ
        start_time = time.time()
        start_time_str = time.strftime("%d-%m-%Y %H:%M:%S", time.localtime(start_time))
        logger.info(f"[SAGA] Programme démarré à : {start_time_str}")
        
        # parametres du programme
        logger.info(f"[SAGA] PARAMETRAGE: mns={chem_mns}, out={chem_out_final}, RepTra={RepTra}, rayon={rayon}, taille_dallage={taille_dallage}, cpu={iNbreCPU}")        
        
        RepTra_tmp=os.path.join(RepTra,"tmp")
        if not os.path.isdir(RepTra): os.mkdir(RepTra)
        if not os.path.isdir(RepTra_tmp): os.mkdir(RepTra_tmp)

        #
        chem_pente_filtree=os.path.join(RepTra_tmp,'pente_filtree.tif')
        Calculer_pente_filtree(chem_mns, RepTra_tmp, chem_pente_filtree, percentile, taille_voisinage, seuil_diff)

        time_tmp = time.time()
        duration_tmp = time_tmp - start_time
        logger.info(f"FIN Calcule de la carte des pentes & filtre - Durée d'exécution : {duration_tmp:.2f} secondes")        
        #
        chem_pente_par_dallle=os.path.join(RepTra_tmp,'pente_par_dallle.tif')
        Daller_pente(chem_pente_filtree,chem_pente_par_dallle, taille_dallage)
        time_tmp = time.time()
        duration_tmp = time_tmp - start_time
        logger.info(f"FIN Dallage des Pentes - Durée d'exécution : {duration_tmp:.2f} secondes") 

        #
        RepTra_DALLAGE_tmp=os.path.join(RepTra_tmp,"DALLAGE")
        if not os.path.isdir(RepTra_DALLAGE_tmp): os.mkdir(RepTra_DALLAGE_tmp)
        
        #
        logger.info(f"BEGIN Dallage du Chantier avec rasterio")
        Decouper_image_en_dalles(chem_mns, taille_dallage, RepTra_DALLAGE_tmp, 'DALLAGE_')
        time_tmp = time.time()
        duration_tmp = time_tmp - start_time
        logger.info(f"FIN Dallage du Chantier avec rasterio - Durée d'exécution : {duration_tmp:.2f} secondes")         

        #
        RepTra_OUT_SAGA_tmp=os.path.join(RepTra_tmp,"OUT_SAGA_tmp")
        if not os.path.isdir(RepTra_OUT_SAGA_tmp): os.mkdir(RepTra_OUT_SAGA_tmp)
        run_saga_par_dalle_parallel_avec_carte_pentes(RepTra_DALLAGE_tmp,RepTra_OUT_SAGA_tmp,chem_pente_par_dallle,taille_dallage,rayon,no_data_ext,iNbreCPU)
        time_tmp = time.time()
        duration_tmp = time_tmp - start_time
        logger.info(f"FIN RUN de SAGA par dalle en // - Durée d'exécution : {duration_tmp:.2f} secondes")  

        RepTra_OUT_SAGA_tmp_expand = os.path.expanduser(RepTra_OUT_SAGA_tmp)
        chem_out_final_tmp=os.path.join(RepTra_tmp,'out_final_tmp.tif')
        chem_out_final_expand_tmp  = os.path.expanduser(chem_out_final_tmp)
        
        # Créer la liste des tâches gdal
        tasks_gdal = []
        for root, dirs, files in os.walk(RepTra_OUT_SAGA_tmp_expand):
            for f in files:
                if f.startswith('ground') and f.endswith('sdat'):
                    chem_in = os.path.join(root, f)
                    chem_out = f"{chem_in[:-5]}.tif"
                    cmd = f"gdal_translate {chem_in} {chem_out}"
                    tasks_gdal.append(cmd)
                    logger.info(cmd)
        
        # Utiliser le Pool de multiprocessing
        # Utiliser imap_unordered pour traiter les commandes en parallèle
        ## NE JAMAIS UTILISER OS.SYSTEM DANS LA PARALLELISATION >> results = list(tqdm(pool.imap_unordered(os.system, tasks_gdal), total=len(tasks_gdal), desc="Convertir les .sdat de SAGA en .tif"))
        with Pool(processes=iNbreCPU) as pool:
            list(tqdm(pool.imap_unordered(run_task_sans_SORTIEMESSAGE, tasks_gdal), total=len(tasks_gdal), desc="Convertir les .sdat de SAGA en .tif avec gdal_translate"))

        time_tmp = time.time()
        duration_tmp = time_tmp - start_time
        logger.info(f"FIN Conversion des .sdat de SAGA en .tif en // - Durée d'exécution : {duration_tmp:.2f} secondes")  

        RepTra_raboutage_tmp=os.path.join(RepTra_OUT_SAGA_tmp,'RABOUTAGE_tmp')

        # 
        if not os.path.isdir(RepTra_raboutage_tmp): 
            os.mkdir(RepTra_raboutage_tmp)
        else:
            shutil.rmtree(RepTra_raboutage_tmp)
            os.mkdir(RepTra_raboutage_tmp)
        logger.info(f"RepTra_raboutage_tmp : {RepTra_raboutage_tmp}")

        RepTra_raboutage_tmp_expand=  os.path.expanduser(RepTra_raboutage_tmp)

        ############################################################################################################
        Raboutage_DALLAGE_SAGA(RepTra_OUT_SAGA_tmp_expand,RepTra_raboutage_tmp_expand,chem_out_final_expand_tmp,iNbreCPU)
    
        ################################################
        end_time=time.time()
        
        time_tmp = time.time()
        duration_tmp = time_tmp - start_time
        logger.info(f"[SAGA] FIN Assemblage des ground.tif par paquet, avec gdal_merge, en // - Durée d'exécution : {duration_tmp:.2f} secondes")  
        #print(f"[SAGA] FIN Assemblage des ground.tif par paquet, avec gdal_merge, en // - Durée d'exécution : {duration_tmp:.2f} secondes")  
        #
        chem_out_final_expand  = os.path.expanduser(chem_out_final)
        Creer_image_binaire(chem_out_final_expand_tmp, chem_out_final_expand, no_data_ext)
        
        # Enregistrer l'heure de fin
        end_time = time.time()
        end_time_str = time.strftime("%d-%m-%Y %H:%M:%S", time.localtime(end_time))
        # Calculer la durée
        duration = end_time - start_time
        logger.info(f"[SAGA] END - Programme terminé à : {end_time_str} - Durée d'exécution : {duration:.2f} secondes")

        logger.info("[SAGA] Fin de main_saga_ground_extraction")
#==================================================================================================
# Gestion des exceptions
#==================================================================================================
    except (RuntimeError, TypeError, NameError):
        print ("ERREUR: ", NameError)

############################################################################################################
#def main_saga_ground_extraction(args):
def main_saga_ground_extraction(chem_mns, chem_out_final, RepTra, iNbreCPU, rayon, taille_dallage, no_data_ext, pente, taille_voisinage=5, K=2, percentile=5, seuil_diff=15):
    
    try:

        logger.info("[SAGA] Démarrage de main_saga_ground_extraction")

        # Enregistrer l'heure de départ
        start_time = time.time()
        start_time_str = time.strftime("%d-%m-%Y %H:%M:%S", time.localtime(start_time))
        logger.info(f"[SAGA] Programme démarré à : {start_time_str}")
        
        # parametres du programme
        logger.info(f"[SAGA] PARAMETRAGE: mns={chem_mns}, out={chem_out_final}, RepTra={RepTra}, rayon={rayon}, taille_dallage={taille_dallage}, cpu={iNbreCPU}")        
        
        RepTra_tmp=os.path.join(RepTra,"tmp")
        if not os.path.isdir(RepTra): os.mkdir(RepTra)
        if not os.path.isdir(RepTra_tmp): os.mkdir(RepTra_tmp)

        #
        RepTra_DALLAGE_tmp=os.path.join(RepTra_tmp,"DALLAGE")
        if not os.path.isdir(RepTra_DALLAGE_tmp): os.mkdir(RepTra_DALLAGE_tmp)
        
        #
        logger.info(f"BEGIN Dallage du Chantier avec rasterio")
        Decouper_image_en_dalles(chem_mns, taille_dallage, RepTra_DALLAGE_tmp, 'DALLAGE_')
        time_tmp = time.time()
        duration_tmp = time_tmp - start_time
        logger.info(f"FIN Dallage du Chantier avec rasterio - Durée d'exécution : {duration_tmp:.2f} secondes") 

        #
        RepTra_OUT_SAGA_tmp=os.path.join(RepTra_tmp,"OUT_SAGA_tmp")
        if not os.path.isdir(RepTra_OUT_SAGA_tmp): os.mkdir(RepTra_OUT_SAGA_tmp)
        #
        logger.info(f"BEGIN RUN de SAGA par dalle en parallèle")
        run_saga_par_dalle_parallel(RepTra_DALLAGE_tmp,RepTra_OUT_SAGA_tmp,rayon,no_data_ext,pente,iNbreCPU)
        time_tmp = time.time()
        duration_tmp = time_tmp - start_time
        logger.info(f"FIN RUN de SAGA par dalle en // - Durée d'exécution : {duration_tmp:.2f} secondes")  

        RepTra_OUT_SAGA_tmp_expand = os.path.expanduser(RepTra_OUT_SAGA_tmp)
        chem_out_final_tmp=os.path.join(RepTra_tmp,'out_final_tmp.tif')
        chem_out_final_expand_tmp  = os.path.expanduser(chem_out_final_tmp)
        
        # Créer la liste des tâches gdal
        tasks_gdal = []
        for root, dirs, files in os.walk(RepTra_OUT_SAGA_tmp_expand):
            for f in files:
                if f.startswith('ground') and f.endswith('sdat'):
                    chem_in = os.path.join(root, f)
                    chem_out = f"{chem_in[:-5]}.tif"
                    cmd = f"gdal_translate {chem_in} {chem_out}"
                    tasks_gdal.append(cmd)
                    logger.info(cmd)
        
        # Utiliser le Pool de multiprocessing
        # Utiliser imap_unordered pour traiter les commandes en parallèle
        ## NE JAMAIS UTILISER OS.SYSTEM DANS LA PARALLELISATION >> results = list(tqdm(pool.imap_unordered(os.system, tasks_gdal), total=len(tasks_gdal), desc="Convertir les .sdat de SAGA en .tif"))
        with Pool(processes=iNbreCPU) as pool:
            list(tqdm(pool.imap_unordered(run_task_sans_SORTIEMESSAGE, tasks_gdal), total=len(tasks_gdal), desc="Convertir les .sdat de SAGA en .tif avec gdal_translate"))

        time_tmp = time.time()
        duration_tmp = time_tmp - start_time
        logger.info(f"FIN Conversion des .sdat de SAGA en .tif en // - Durée d'exécution : {duration_tmp:.2f} secondes")  

        RepTra_raboutage_tmp=os.path.join(RepTra_OUT_SAGA_tmp,'RABOUTAGE_tmp')

        # 
        if not os.path.isdir(RepTra_raboutage_tmp): 
            os.mkdir(RepTra_raboutage_tmp)
        else:
            shutil.rmtree(RepTra_raboutage_tmp)
            os.mkdir(RepTra_raboutage_tmp)
        logger.info(f"RepTra_raboutage_tmp : {RepTra_raboutage_tmp}")

        RepTra_raboutage_tmp_expand=  os.path.expanduser(RepTra_raboutage_tmp)

        ############################################################################################################
        Raboutage_DALLAGE_SAGA(RepTra_OUT_SAGA_tmp_expand,RepTra_raboutage_tmp_expand,chem_out_final_expand_tmp,iNbreCPU)
    
        ################################################
        end_time=time.time()
        
        time_tmp = time.time()
        duration_tmp = time_tmp - start_time
        logger.info(f"[SAGA] FIN Assemblage des ground.tif par paquet, avec gdal_merge, en // - Durée d'exécution : {duration_tmp:.2f} secondes")  
        #print(f"[SAGA] FIN Assemblage des ground.tif par paquet, avec gdal_merge, en // - Durée d'exécution : {duration_tmp:.2f} secondes")  
        #
        chem_out_final_expand  = os.path.expanduser(chem_out_final)
        Creer_image_binaire(chem_out_final_expand_tmp, chem_out_final_expand, no_data_ext)
        
        # Enregistrer l'heure de fin
        end_time = time.time()
        end_time_str = time.strftime("%d-%m-%Y %H:%M:%S", time.localtime(end_time))
        # Calculer la durée
        duration = end_time - start_time
        logger.info(f"[SAGA] END - Programme terminé à : {end_time_str} - Durée d'exécution : {duration:.2f} secondes")

        logger.info("[SAGA] Fin de main_saga_ground_extraction")
#==================================================================================================
# Gestion des exceptions
#==================================================================================================
    except (RuntimeError, TypeError, NameError):
        print ("ERREUR: ", NameError)

############################################################################################################
if __name__ == "__main__":
    #
    args = parse_arguments()
    #
    # taille_voisinage=5 
    # K=2
    # percentile=5
    # seuil_diff=15
    #
    chem_mns = args.mns
    RepTra = args.RepTra
    chem_out_final = args.out
    iNbreCPU=args.cpu
    rayon=args.radius
    taille_dallage=args.tile
    no_data_ext=args.nodata_ext
    #

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file_path = os.path.join(os.path.dirname(chem_out_final), f"log_{timestamp}.txt")  
    logger.remove()
    logger.add(log_file_path, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
    start_time = time.time()
    start_time_str = time.strftime("%d-%m-%Y %H:%M:%S", time.localtime(start_time))
    logger.info(f"Programme main_saga_ground_extraction démarré à : {start_time_str}")
        
    main_saga_ground_extraction(chem_mns, chem_out_final, RepTra, iNbreCPU, rayon, taille_dallage, no_data_ext)
        
    # Arrêter le chronomètre et calculer le temps écoulé
    end_time = time.time()
    elapsed_time = end_time - start_time  # Temps écoulé en secondes
        
    #Convertir le temps écoulé en heures, minutes, secondes
    formatted_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

    # Afficher le temps total de traitement
    logger.info(f"Temps total de traitement dans main_saga_ground_extraction: {formatted_time}")       
		
    logger.info("END main_saga_ground_extraction")        