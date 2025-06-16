#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
import shutil
from SAGA.script_saga_ground_extraction import main_saga_ground_extraction
import subprocess
import argparse
import rasterio
from rasterio.windows import Window
from rasterio.windows import from_bounds
import numpy as np
from multiprocessing import Pool
from tqdm import tqdm
import signal
import random
from scipy.spatial import distance_matrix
from scipy.interpolate import griddata
from scipy.interpolate import RBFInterpolator
from scipy.interpolate import LinearNDInterpolator
from loguru import logger

os.environ['OMP_NUM_THREADS'] = '1'

cmd_gemo_unit='main_GEMAUT_unit'  

####################################################################################################
def GetNbLignes(chemMNS):
    # Utilisation de rasterio pour obtenir la hauteur (nombre de lignes)
    try:
        with rasterio.open(chemMNS) as dataset:
            return dataset.height
    except Exception as e:
        print("Erreur lors de l'ouverture ou de la lecture du fichier :", e)
        return None

####################################################################################################
def GetNbColonnes(chemMNS):
    # Utilisation de rasterio pour obtenir la largeur (nombre de colonnes)
    try:
        with rasterio.open(chemMNS) as dataset:
            return dataset.width
    except Exception as e:
        print("Erreur lors de l'ouverture ou de la lecture du fichier :", e)
        return None
    
#################################################################################################### 
def init_worker():
	signal.signal(signal.SIGINT, signal.SIG_IGN)

####################################################################################################
# Fonction pour exécuter une commande quelconque (notamment gdal) via subprocess
def run_task_sans_SORTIEMESSAGE(cmd):
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

############################################################################################################
def dallage_pente(chem_pente_filtree,chem_pente_par_dallle,taille_carre):
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

##################################################################################################################
def Raboutage_OTB_BUG(RepTravail_tmp,NbreDalleX,NbreDalleY,chemMNT_OUT):
    #### Assemblage final - avec OTB buggué
    cmd_blending_otb='otbcli_Mosaic'
    cmd_blending="%s -il " %cmd_blending_otb
                
    ## lancement de LSL sur chaque dalle    
    for x in range(NbreDalleX):
        for y in range(NbreDalleY):
            ## Nom de la dalle courante
            RepDalleXY=os.path.join(RepTravail_tmp,"Dalle_%s_%s"%(x,y))
            chem_out=os.path.join(RepDalleXY,"Out_MNT_%s_%s.tif"%(x,y))
            cmd_blending_tmp="%s %s " %(cmd_blending,chem_out)
            cmd_blending=cmd_blending_tmp
                    
    cmd_blending_final="%s -comp.feather large -out %s -progress 0 " %(cmd_blending,chemMNT_OUT)
    # à décommenter # print(cmd_blending_final)
    os.system(cmd_blending_final)   

##################################################################################################################
def calculer_masque_ponderation(width, height, axis):
    """
    Calcule un masque de pondération linéaire en fonction de la distance au bord.
    `axis=1` pour une pondération horizontale (largeur), `axis=0` pour une pondération verticale (hauteur).
    """
    if axis == 1:
        x = np.linspace(0, 1, width)
        mask = np.tile(x, (height, 1))
    else:
        y = np.linspace(0, 1, height)
        mask = np.tile(y[:, np.newaxis], (1, width))

    return mask
    
##################################################################################################################
def sauvegarder_chevauchement(src, window, output_dir):
    # Extraire les données de la fenêtre
    data = src.read(1, window=window)
    
    # Calculer les coordonnées en haut à gauche de la fenêtre
    x_min, y_max = rasterio.windows.transform(window, src.transform) * (0, 0)

    # Générer un nombre aléatoire entre 1 et 1000
    random_number = random.randint(1, 1000)

    # Créer un nom de fichier basé sur les coordonnées
    filename = f"chevauchement_{x_min:.6f}_{y_max:.6f}_{random_number}.tif"
    output_path = os.path.join(output_dir, filename)
    
    # Créer un profil ajusté pour la fenêtre
    profile = src.profile.copy()
    profile.update({
        'height': window.height,
        'width': window.width,
        'transform': rasterio.windows.transform(window, src.transform)
    })
    
    # Sauvegarder les données dans le fichier de sortie avec le nom géoréférencé
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(data, 1)
    
##################################################################################################################
def obtenir_zone_chevauchement(src1, src2):
    """
    Calcule les fenêtres et la zone de chevauchement entre deux images géoréférencées.
    """
    # Calculer l'étendue commune en coordonnées géographiques
    bounds1 = src1.bounds
    bounds2 = src2.bounds
    intersection_bounds = (
        max(bounds1.left, bounds2.left),
        max(bounds1.bottom, bounds2.bottom),
        min(bounds1.right, bounds2.right),
        min(bounds1.top, bounds2.top)
    )
    if intersection_bounds[0] >= intersection_bounds[2] or intersection_bounds[1] >= intersection_bounds[3]:
        raise ValueError("Les images ne se chevauchent pas.")
    # Conversion des coordonnées d'intersection en fenêtres (indices des pixels)
    window1 = from_bounds(*intersection_bounds, src1.transform)
    window2 = from_bounds(*intersection_bounds, src2.transform)

    return window1, window2

##################################################################################################################
def save_raster(data, filename, profile):
    """
    Sauvegarde une image raster en utilisant rasterio.
    :param data: tableau NumPy contenant les données de l'image.
    :param filename: chemin du fichier où sauvegarder l'image.
    :param profile: profil de l'image source, utilisé pour la géoréférenciation.
    """
    with rasterio.open(filename, 'w', **profile) as dst:
        dst.write(data, 1)

##################################################################################################################
def Raboutage(RepTravail_tmp, NbreDalleX, NbreDalleY, chemMNT_OUT):
    #
    # total_steps = (NbreDalleY * (NbreDalleX - 1)) + 2 * NbreDalleY    
    total_steps = (NbreDalleY * NbreDalleX ) + NbreDalleY + 1
    with tqdm(total=total_steps, desc="Progression globale", unit="étape") as pbar:

        #ligne_mosaics = []

        for y in range(NbreDalleY):
            ligne_dalles = []

            for x in range(NbreDalleX):
                chem_dalle = os.path.join(RepTravail_tmp, f"Dalle_{x}_{y}", f"Out_MNT_{x}_{y}.tif")

                with rasterio.open(chem_dalle) as src:
                    profile = src.profile

                    if x > 0:
                        # Fusion avec la dalle précédente
                        prev_dalle_path = ligne_dalles[-1]
                        with rasterio.open(prev_dalle_path) as src_prev:
                            prev_dalle = src_prev.read(1)

                            # Obtenir zone de chevauchement
                            window_prev, window_curr = obtenir_zone_chevauchement(src_prev, src)
                            chevauchement_prev = src_prev.read(1, window=window_prev)
                            chevauchement_curr = src.read(1, window=window_curr)

                            # Créer les masques de pondération
                            largeur, hauteur = chevauchement_curr.shape[1], chevauchement_curr.shape[0]
                            mask_droite = calculer_masque_ponderation(largeur, hauteur, axis=1)
                            mask_gauche = 1 - mask_droite

                            # Fusion pondérée
                            fusion = (chevauchement_prev * mask_gauche + chevauchement_curr * mask_droite)
                            prev_dalle[:, -largeur:] = fusion  
                            dalle = src.read(1) 
                            dalle = dalle[:, largeur:]  

                            # Enregistrer prev_dalle fusionnée dans le fichier d'origine
                            # Mise à jour du profil pour la nouvelle taille de la mosaïque de la ligne

                            with rasterio.open(prev_dalle_path, 'w', **src_prev.profile) as dst_prev:
                                dst_prev.write(prev_dalle, 1)

                            # Création d'un profil de culture pour la dalle corrigée
                            src_crop = src.profile.copy()
                            src_crop.update(
                                width=dalle.shape[1],
                                height=dalle.shape[0],
                                transform=src.window_transform(rasterio.windows.Window(largeur, 0, dalle.shape[1], dalle.shape[0]))  # Ajustement pour décaler la transformation
                            )

                            # Enregistrer la dalle corrigée dans un nouveau fichier avec le profil mis à jour
                            temp_dalle_path = os.path.join(RepTravail_tmp, f"Dalle_corrigee_{x}_{y}.tif")
                            with rasterio.open(temp_dalle_path, 'w', **src_crop) as dst:
                                dst.write(dalle, 1)

                    else:
                        dalle = src.read(1)
                        # Enregistrer la dalle actuelle (corrigée si fusionnée)
                        temp_dalle_path = os.path.join(RepTravail_tmp, f"Dalle_corrigee_{x}_{y}.tif")
                        with rasterio.open(temp_dalle_path, 'w', **profile) as dst:
                            dst.write(dalle, 1)

                    # Ajouter le chemin du fichier corrigé
                    ligne_dalles.append(temp_dalle_path)
                    pbar.update(1)

            # Construction de la mosaïque pour la ligne sans chevauchement
            ligne_dalles_data = []
            for path in ligne_dalles:
                with rasterio.open(path) as src:
                    data = src.read(1)
                    ligne_dalles_data.append(data)

            # Concatenation de la ligne en tenant compte des corrections
            ligne_mosaic = np.concatenate(ligne_dalles_data, axis=1)

            # Récupération des informations de géoréférencement à partir de la première dalle
            with rasterio.open(ligne_dalles[0]) as src:
                transform = src.transform  # Transformation affine de la première dalle
                crs = src.crs              # Système de projection (CRS)
                profile = src.profile      # Profil pour la création du fichier GeoTIFF

            # Mise à jour du profil pour la nouvelle taille de la mosaïque de la ligne
            profile.update(
                width=ligne_mosaic.shape[1],  # Largeur de la mosaïque
                height=ligne_mosaic.shape[0],  # Hauteur de la mosaïque
                transform=transform,  # Utiliser la transformation géoréférencée de la première dalle
                crs=crs,  # Utiliser le même CRS que la dalle d'origine
                count=1,  # Une seule bande dans le fichier
                dtype=rasterio.float32  # Type de données, à ajuster si nécessaire
            )

            # Sauvegarder la mosaïque de la ligne en GeoTIFF
            output_path = os.path.join(RepTravail_tmp, f"ligne_mosaic_{y}.tif")
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(ligne_mosaic, 1)  # Écrire la mosaïque dans le fichier GeoTIFF

            pbar.update(1)

#######################################

    # Initialiser la liste des mosaïques de lignes
    all_mosaics = []

    for y in range(NbreDalleY):

        output_path = os.path.join(RepTravail_tmp, f"ligne_mosaic_{y}.tif")

        with rasterio.open(output_path) as src:
            profile = src.profile 

            if y > 0:

                # Fusion avec la mosaïque de ligne précédente
                prev_mosaic_path = all_mosaics[-1]
                with rasterio.open(prev_mosaic_path) as src_prev:
                    prev_mosaic = src_prev.read(1)
                    # Obtenir la zone de chevauchement vertical 
                    window_prev, window_curr = obtenir_zone_chevauchement(src_prev, src)
                    chevauchement_prev = src_prev.read(1, window=window_prev)
                    chevauchement_curr = src.read(1, window=window_curr)
                    largeur, hauteur = chevauchement_curr.shape[1], chevauchement_curr.shape[0]
                    mask_bas = calculer_masque_ponderation(largeur, hauteur, axis=0)
                    mask_haut = 1 - mask_bas
                    # Fusion pondérée des chevauchements
                    fusion = (chevauchement_prev * mask_haut + chevauchement_curr * mask_bas)
                    prev_mosaic[-hauteur:, :] = fusion
                    ligne_mosaic = src.read(1)
                    ligne_mosaic = ligne_mosaic[hauteur:, :]

                    with rasterio.open(prev_mosaic_path, 'w', **src_prev.profile) as dst_prev:
                        dst_prev.write(prev_mosaic, 1)                
                

                    src_crop = src.profile.copy()
                    src_crop.update(
                        width=ligne_mosaic.shape[1],
                        height=ligne_mosaic.shape[0],
                        transform=src.window_transform(rasterio.windows.Window(0, hauteur, ligne_mosaic.shape[1], ligne_mosaic.shape[0]))  # Ajustement pour décaler la transformation
                    )

                    # Enregistrer la dalle corrigée dans un nouveau fichier avec le profil mis à jour
                    temp_mosaic_path = os.path.join(RepTravail_tmp, f"ligne_mosaic_CORRIGEE_{y}.tif")
                    with rasterio.open(temp_mosaic_path, 'w', **src_crop) as dst:
                        dst.write(ligne_mosaic, 1)

            else:

                ligne_mosaic = src.read(1)
                temp_mosaic_path = os.path.join(RepTravail_tmp, f"ligne_mosaic_CORRIGEE_{y}.tif")
                #
                with rasterio.open(temp_mosaic_path, 'w', **profile) as dst:
                    dst.write(ligne_mosaic, 1)

            # Ajouter le chemin du fichier corrigé
            all_mosaics.append(temp_mosaic_path)
            pbar.update(1)
                                
    # Construction de la mosaïque pour la ligne sans chevauchement
    all_mosaics_data = []
    for path in all_mosaics:
        with rasterio.open(path) as src:
            data = src.read(1)
            all_mosaics_data.append(data)

    # Concatenation de la ligne en tenant compte des corrections
    mosaic_final = np.concatenate(all_mosaics_data, axis=0)
    
    # Récupération des informations de géoréférencement à partir de la première dalle
    with rasterio.open(all_mosaics[0]) as src:
        transform = src.transform  # Transformation affine de la première dalle
        crs = src.crs              # Système de projection (CRS)
        profile = src.profile      # Profil pour la création du fichier GeoTIFF

    # Mise à jour du profil pour la nouvelle taille de la mosaïque de la ligne
    profile.update(
        width=mosaic_final.shape[1],  # Largeur de la mosaïque
        height=mosaic_final.shape[0],  # Hauteur de la mosaïque
        transform=transform,  # Utiliser la transformation géoréférencée de la première dalle
        crs=crs,  # Utiliser le même CRS que la dalle d'origine
        count=1,  # Une seule bande dans le fichier
        dtype=rasterio.float32  # Type de données, à ajuster si nécessaire
    )
    # Sauvegarder la mosaïque de la ligne en GeoTIFF
    with rasterio.open(chemMNT_OUT, 'w', **profile) as dst:
            dst.write(mosaic_final, 1)  # Écrire la mosaïque dans le fichier GeoTIFF

    logger.info(f"Ligne mosaïque sauvegardée sous {chemMNT_OUT}")
    pbar.update(pbar.total - pbar.n) 

#################################################################################################### 
### calcule le nombre de dalles en X et en Y en fonction des paramètres de chantier
def CalculNombreDallesXY(NbColonnes,NbLignes,Taille_dalle,Recouv_entre_dalles):
        
    ### pour calculer le nombre de dalles en X et en Y        
    NumX=NbColonnes-Taille_dalle
    NumY=NbLignes-Taille_dalle
    Denom=Taille_dalle-Recouv_entre_dalles
        
    ### Calcul du nombre de dalles en X        
    if (NumX%Denom == 0):
        NbreDalleX=NumX/Denom+1
    else: 
        NbreDalleX=int((NumX/Denom)+1)+1
        
    ### Calcul du nombre de dalles en Y        
    if (NumY%Denom == 0):
        NbreDalleY=NumY/Denom+1
    else: 
        NbreDalleY=int((NumY/Denom)+1)+1
    
    return (NbreDalleX,NbreDalleY)

####################################################################################################
def GetInfo(chemMNS):
    
    with rasterio.open(chemMNS) as dataset:
        # Récupération des métadonnées de base
        PasX = dataset.transform[0]  # Taille de pixel en X
        PasY = dataset.transform[4]  # Taille de pixel en Y
        X_0 = dataset.bounds.left     # Position X (GAUCHE)
        X_1 = dataset.bounds.right    # Position X (DROITE)
        Y_0 = dataset.bounds.bottom   # Position Y (BAS)
        Y_1 = dataset.bounds.top      # Position Y (HAUT)

        # Code EPSG pour la projection
        Projection = dataset.crs.to_epsg() if dataset.crs else -1

        # Dimensions
        NbreCol = dataset.width
        NbreLig = dataset.height
            
        # Récupération de GModel depuis les tags de métadonnées (si disponible)
        tags = dataset.tags()
            
        # Détermination de GRaster et phasage basé sur AREA_OR_POINT
        area_or_point = tags.get("AREA_OR_POINT", "Area")  # "Point" signifie CP, "Area" signifie HG
            
        return [PasX, PasY, Projection, X_0, X_1, Y_0, Y_1, area_or_point, NbreCol, NbreLig]

############################################################################################################################         
def GetNbreDalleXDalleY(chemMNS_SousEch, iTailleparcelle, iTailleRecouvrement):
    """
    Calcule le nombre de dalles nécessaires en X et Y.
    Gère le cas où l'image est plus petite que la taille de dalle demandée.
    """
    # Ouvrir le fichier raster
    with rasterio.open(chemMNS_SousEch) as src:
        # Obtenir les dimensions de l'image
        NbreCol = src.width  # Nombre de colonnes
        NbreLig = src.height  # Nombre de lignes
        
    logger.info(f"Dimensions de l'image : {NbreCol}x{NbreLig}")
    logger.info(f"Taille de dalle demandée : {iTailleparcelle}x{iTailleparcelle}")
    logger.info(f"Recouvrement : {iTailleRecouvrement}")

    # Si l'image est plus petite que la taille de dalle demandée
    if NbreCol <= iTailleparcelle and NbreLig <= iTailleparcelle:
        logger.warning(f"L'image ({NbreCol}x{NbreLig}) est plus petite que la taille de dalle demandée ({iTailleparcelle}x{iTailleparcelle})")
        logger.warning("Utilisation d'une seule dalle aux dimensions de l'image")
        return 1, 1

    # Calcul standard pour les grandes images
    NumX = NbreCol - iTailleparcelle
    NumY = NbreLig - iTailleparcelle
    Denom = iTailleparcelle - iTailleRecouvrement
        
    # Calcul du nombre de dalles en X        
    if (NumX <= 0):
        NbreDalleX = 1
    elif (NumX % Denom == 0):
        NbreDalleX = NumX/Denom + 1
    else: 
        NbreDalleX = int((NumX/Denom) + 1) + 1
        
    # Calcul du nombre de dalles en Y        
    if (NumY <= 0):
        NbreDalleY = 1
    elif (NumY % Denom == 0):
        NbreDalleY = NumY/Denom + 1
    else: 
        NbreDalleY = int((NumY/Denom) + 1) + 1
    
    logger.info(f"Nombre de dalles calculé : {NbreDalleX}x{NbreDalleY}")
    return (int(NbreDalleX), int(NbreDalleY))

#################################################################################################### 
def RunGemoEnParallel(RepTravail_tmp, NbreDalleX, NbreDalleY, fsigma, flambda, norme, no_data_value, iNbreCPU):
    
    tasks = []
    logger.info(f"Début de RunGemoEnParallel dans {RepTravail_tmp}")
    logger.info(f"Nombre de dalles : {NbreDalleX}x{NbreDalleY}")

    # Vérifier d'abord l'existence du répertoire de travail
    if not os.path.exists(RepTravail_tmp):
        raise ValueError(f"Répertoire de travail non trouvé : {RepTravail_tmp}")

    for x in range(NbreDalleX):
        for y in range(NbreDalleY):
            RepDalleXY = os.path.join(RepTravail_tmp, f"Dalle_{x}_{y}")
            logger.debug(f"Vérification de la dalle {x},{y} dans {RepDalleXY}")

            if not os.path.exists(RepDalleXY):
                logger.warning(f"Répertoire de dalle manquant : {RepDalleXY}")
                continue

            ChemOUT_mns = os.path.join(RepDalleXY, f"Out_MNS_{x}_{y}.tif")
            ChemOUT_masque = os.path.join(RepDalleXY, f"Out_MASQUE_{x}_{y}.tif")
            ChemOUT_INIT = os.path.join(RepDalleXY, f"Out_INIT_{x}_{y}.tif")
            ChemOUT_mnt = os.path.join(RepDalleXY, f"Out_MNT_{x}_{y}.tif")

            # Vérifier l'existence des fichiers nécessaires
            if not os.path.exists(ChemOUT_mns):
                logger.error(f"Fichier MNS manquant : {ChemOUT_mns}")
                continue

            try:
                if contient_donnees(ChemOUT_mns, no_data_value):
                    cmd_unitaire = f"{cmd_gemo_unit} {ChemOUT_mns} {ChemOUT_masque} {ChemOUT_INIT} {ChemOUT_mnt} {fsigma} {flambda} {no_data_value} {norme}"
                    logger.debug(f"Ajout de la commande : {cmd_unitaire}")
                    tasks.append(cmd_unitaire)
                else:
                    logger.info(f"Dalle {x},{y} sans données valides, copie directe")
                    shutil.copyfile(ChemOUT_mns, ChemOUT_mnt)
            except Exception as e:
                logger.error(f"Erreur lors du traitement de la dalle {x},{y}: {str(e)}")
                continue

    if not tasks:
        logger.warning("Aucune tâche à exécuter !")
        return

    logger.info(f"Lancement de {len(tasks)} tâches en parallèle")
    with Pool(processes=iNbreCPU, initializer=init_worker) as pool:
        try:
            results = list(tqdm(pool.imap_unordered(os.system, tasks), 
                              total=len(tasks), 
                              desc="Lancement de GEMO unitaire en parallèle"))
            logger.info("Traitement parallèle terminé avec succès")
        except Exception as e:
            logger.error(f"Erreur durant le traitement parallèle : {str(e)}")
            raise

    return

####################################################################################################
def contient_donnees(chem_mns, no_data_value=-9999):
    """
    Vérifie si une dalle contient des données valides.
    :param chem_mns: chemin vers le MNS.
    :param no_data_value: Valeur correspondant à "no data".
    :return: True si la dalle contient des données valides, False sinon.
    """
    # Ouvrir l'image raster
    with rasterio.open(chem_mns) as src:
        # Lire les données du raster dans un tableau numpy
        data = src.read(1)  # Lecture de la première bande 
        return not np.all(data == no_data_value)

####################################################################################################
def Decoupe_dalle(args):
    """
    Fonction qui traite une dalle sur les 3 entrées de GEMO.
    """
    mns_file, masque_file, init_file, col_dalle, lig_dalle, x_offset, y_offset, l_dalle, h_dalle, no_data_value, RepTravail_tmp = args

    try:
        RepDalleXY = os.path.join(RepTravail_tmp, f"Dalle_{col_dalle}_{lig_dalle}")
        logger.info(f"Traitement de la dalle {col_dalle}_{lig_dalle}")
        logger.debug(f"Paramètres: offset=({x_offset},{y_offset}), taille=({l_dalle},{h_dalle})")

        # Créer le répertoire de la dalle
        os.makedirs(RepDalleXY, exist_ok=True)
        logger.debug(f"Répertoire créé/vérifié : {RepDalleXY}")

        # Vérifier l'existence des fichiers source
        for f in [mns_file, masque_file, init_file]:
            if not os.path.exists(f):
                logger.error(f"Fichier source manquant : {f}")
                raise FileNotFoundError(f"Fichier source manquant : {f}")

        # Lire et découper les trois images
        with rasterio.open(mns_file) as mns_src, \
             rasterio.open(masque_file) as masque_src, \
             rasterio.open(init_file) as init_src:
            
            # Si l'image est plus petite que la taille de dalle demandée,
            # utiliser les dimensions de l'image
            if l_dalle > mns_src.width:
                l_dalle = mns_src.width
                logger.warning(f"Largeur de dalle ajustée à la largeur de l'image : {l_dalle}")
            if h_dalle > mns_src.height:
                h_dalle = mns_src.height
                logger.warning(f"Hauteur de dalle ajustée à la hauteur de l'image : {h_dalle}")

            window = Window(x_offset, y_offset, l_dalle, h_dalle)
            logger.debug(f"Fenêtre de lecture : {window}")
            
            # Lire les dalles
            try:
                mns_dalle = mns_src.read(1, window=window)
                masque_dalle = masque_src.read(1, window=window)
                init_dalle = init_src.read(1, window=window)
                logger.debug(f"Dalles lues avec succès: shapes={mns_dalle.shape}")
            except Exception as e:
                logger.error(f"Erreur lors de la lecture des dalles : {e}")
                raise

            # Construire les chemins de sortie
            fichiers_dalles = {
                "mns": os.path.join(RepDalleXY, f"Out_MNS_{col_dalle}_{lig_dalle}.tif"),
                "masque": os.path.join(RepDalleXY, f"Out_MASQUE_{col_dalle}_{lig_dalle}.tif"),
                "init": os.path.join(RepDalleXY, f"Out_INIT_{col_dalle}_{lig_dalle}.tif")
            }
            
            # Sauvegarder les dalles
            for name, dalle, src in zip(fichiers_dalles.keys(), [mns_dalle, masque_dalle, init_dalle], [mns_src, masque_src, init_src]):
                profil = src.profile.copy()
                profil.update({
                    'height': h_dalle,
                    'width': l_dalle,
                    'transform': src.window_transform(window)
                })
                
                try:
                    with rasterio.open(fichiers_dalles[name], 'w', **profil) as dst:
                        dst.write(dalle, 1)
                    logger.debug(f"Dalle {name} sauvegardée : {fichiers_dalles[name]}")
                except Exception as e:
                    logger.error(f"Erreur lors de la sauvegarde de la dalle {name} : {e}")
                    raise

            logger.info(f"Dalle {col_dalle}_{lig_dalle} traitée avec succès")
            return True

    except Exception as e:
        logger.error(f"Erreur lors du traitement de la dalle {col_dalle}_{lig_dalle}: {str(e)}")
        raise

#################################################################################################### 
# Decoupe_chantier(chemMNS_SousEch_tmp, chemMASQUE_SousEch, chemINIT_SousEch, taille_dalle, iTailleRecouvrement, no_data_ext, RepTravail_tmp, iNbreCPU)
def Decoupe_chantier(mns_file, masque_file, init_file, taille_dalle, iTailleRecouvrement, no_data_value, RepTravail_tmp, iNbreCPU):
    """
    Traite trois grandes images en découpant en dalles avec chevauchement.
    """
    logger.info(f"Début de Decoupe_chantier avec:")
    logger.info(f"- MNS: {mns_file}")
    logger.info(f"- Masque: {masque_file}")
    logger.info(f"- Init: {init_file}")
    logger.info(f"- Répertoire temp: {RepTravail_tmp}")

    # Vérifier et créer le répertoire de travail principal
    if not os.path.exists(RepTravail_tmp):
        try:
            os.makedirs(RepTravail_tmp)
            logger.info(f"Répertoire de travail créé : {RepTravail_tmp}")
        except Exception as e:
            logger.error(f"Impossible de créer le répertoire de travail : {e}")
            raise

    with rasterio.open(mns_file) as mns_src:
        largeur = mns_src.width
        hauteur = mns_src.height
        logger.info(f"DEBUG - Dimensions MNS: {largeur}x{hauteur}")

        h_dalle, l_dalle = taille_dalle
        logger.info(f"DEBUG - Taille dalle: {h_dalle}x{l_dalle}")

        # Si l'image est plus petite que la taille de dalle
        if largeur <= l_dalle or hauteur <= h_dalle:
            logger.warning(f"MNS ({largeur}x{hauteur}) plus petit que la taille de dalle ({l_dalle}x{h_dalle})")
            logger.warning("Utilisation d'une seule dalle aux dimensions du MNS")
            NbreDalleX = 1
            NbreDalleY = 1
            # Ajuster la taille de dalle aux dimensions du MNS
            l_dalle = largeur
            h_dalle = hauteur
            taille_dalle = (h_dalle, l_dalle)
        else:
            # Calculer le pas entre les dalles en fonction du recouvrement
            pas_x = l_dalle - iTailleRecouvrement
            pas_y = h_dalle - iTailleRecouvrement
            logger.info(f"DEBUG - Pas: {pas_x}x{pas_y}, Recouvrement: {iTailleRecouvrement}")

            # Calculer le nombre de dalles avec recouvrement
            NbreDalleX = max(1, (largeur - iTailleRecouvrement + pas_x - 1) // pas_x)
            NbreDalleY = max(1, (hauteur - iTailleRecouvrement + pas_y - 1) // pas_y)

        logger.info(f"DEBUG - Nombre de dalles: {NbreDalleX}x{NbreDalleY}")

        # Créer tous les répertoires des dalles avant le traitement parallèle
        logger.info("DEBUG - Création des répertoires des dalles...")
        for x in range(NbreDalleX):
            for y in range(NbreDalleY):
                RepDalleXY = os.path.join(RepTravail_tmp, f"Dalle_{x}_{y}")
                try:
                    os.makedirs(RepDalleXY, exist_ok=True)
                    logger.debug(f"Répertoire créé : {RepDalleXY}")
                except Exception as e:
                    logger.error(f"Impossible de créer le répertoire {RepDalleXY}: {e}")
                    raise

        # Créer une liste des paramètres pour chaque dalle
        params = []
        for x in range(NbreDalleX):
            for y in range(NbreDalleY):
                if NbreDalleX == 1 and NbreDalleY == 1:
                    # Cas d'une seule dalle : utiliser toute l'image
                    x_offset = 0
                    y_offset = 0
                    l_bloc = largeur
                    h_bloc = hauteur
                else:
                    # Calcul normal pour plusieurs dalles
                    x_offset = x * pas_x
                    y_offset = y * pas_y
                    l_bloc = min(l_dalle, largeur - x_offset)
                    h_bloc = min(h_dalle, hauteur - y_offset)
                
                params.append((mns_file, masque_file, init_file, x, y, x_offset, y_offset, l_bloc, h_bloc, no_data_value, RepTravail_tmp))
                logger.debug(f"Dalle_{x}_{y}: offset=({x_offset},{y_offset}), taille=({l_bloc},{h_bloc})")

        # Utiliser multiprocessing pour traiter les dalles en parallèle
        with Pool(processes=iNbreCPU) as pool:
            try:
                results = list(tqdm(pool.imap_unordered(Decoupe_dalle, params), total=len(params), desc="- Traitement des dalles -"))
                logger.info("Découpage des dalles terminé avec succès")
            except Exception as e:
                logger.error(f"Erreur lors du découpage des dalles : {str(e)}")
                raise

####################################################################################################
def fill_holes_with_interpolation(chemMNS_IN, no_data_int, no_data_ext, e, weight_type, chemMNS_filled):
    with rasterio.open(chemMNS_IN) as src:
        mns = src.read(1)  # Lecture de la première bande dans un tableau NumPy

        # Masque des pixels NoData pour combler uniquement les trous no_data_int
        mask_invalid = (mns == no_data_int)

        # Identifier les indices des pixels valides (hors no_data_int et no_data_ext) et des trous no_data_int
        valid_indices = np.argwhere(~mask_invalid & (mns != no_data_ext))
        hole_indices = np.argwhere(mask_invalid)

        # Extraire les valeurs des pixels valides
        valid_values = mns[valid_indices[:, 0], valid_indices[:, 1]]

        # Masque de pixels de bordure pour l'interpolation autour des trous
        edge_mask = np.zeros_like(mns, dtype=bool)
        for i, j in hole_indices:
            edge_mask[max(0, i - e):min(i + e + 1, mns.shape[0]),
                      max(0, j - e):min(j + e + 1, mns.shape[1])] = True

        # Exclure les pixels NoData et garder uniquement les pixels de bordure
        edge_mask &= ~mask_invalid & (mns != no_data_ext)
        edge_indices = np.argwhere(edge_mask)  # Coordonnées des pixels de bordure

        # Calcul des poids en fonction de la distance pour les pixels de bordure
        if weight_type == 1:  # Distance Euclidienne
            weights = distance_matrix(edge_indices, hole_indices)
        elif weight_type == 2:  # Carré de la distance Euclidienne
            weights = distance_matrix(edge_indices, hole_indices)**2
        elif weight_type == 3:  # Distance L1 (Manhattan)
            weights = distance_matrix(edge_indices, hole_indices, p=1)
        else:
            raise ValueError("Type de poids non supporté.")

        weights = 1 / (weights + 1e-10)  # Inverser la distance pour attribuer un poids plus élevé aux pixels proches

        # Extraire les valeurs des pixels de bordure
        edge_values = mns[edge_indices[:, 0], edge_indices[:, 1]]

        # Appliquer l'interpolation pondérée pour combler les trous no_data_int uniquement
        interpolated_values = griddata(
            edge_indices,  # Points de bordure (connus)
            edge_values,   # Valeurs aux points de bordure
            hole_indices,  # Points à interpoler (trous no_data_int)
            method='linear'  # Interpolation linéaire
        )

        # Remplir les trous avec les valeurs interpolées
        mns_filled = mns.copy()
        for (i, j), val in zip(hole_indices, interpolated_values):
            if not np.isnan(val):  # Ignorer les NaN restants
                mns_filled[i, j] = val

        # Sauvegarde du résultat dans un nouveau fichier
        out_meta = src.meta.copy()
        out_meta.update({
            "dtype": 'float32'  # Type de données pour les valeurs interpolées
        })

        with rasterio.open(chemMNS_filled, 'w', **out_meta) as dst:
            dst.write(mns_filled, 1)

####################################################################################################
def fill_holes_simple_OLD(chemMNS_IN, no_data_int, no_data_ext, chemMNS_filled):
    with rasterio.open(chemMNS_IN) as src:
        mns = src.read(1)  # Lecture de la première bande dans un tableau NumPy

        print("fill_holes_simple - 1")
        # Masque uniquement des pixels no_data_int pour les trous à combler
        mask_invalid = (mns == no_data_int)
        
        print("fill_holes_simple - 2")
        # Identifier les coordonnées des pixels valides (hors no_data_int) et des trous (no_data_int)
        valid_indices = np.argwhere(~mask_invalid & (mns != no_data_ext))  # Coordonnées des pixels valides (non NoData)
        hole_indices = np.argwhere(mask_invalid)                           # Coordonnées des trous (no_data_int uniquement)

        print("fill_holes_simple - 3")
        # Extraire les valeurs des pixels valides (hors no_data_int et no_data_ext)
        valid_values = mns[valid_indices[:, 0], valid_indices[:, 1]]

        print("fill_holes_simple - 4")
        # Interpolation linéaire pour combler les trous (no_data_int uniquement)
        # interpolated_values = griddata(
        #     valid_indices,      # Points valides pour interpolation
        #     valid_values,       # Valeurs aux points valides
        #     hole_indices,       # Points à interpoler (trous no_data_int)
        #     method='linear'     # Interpolation linéaire
        # )

        # Créer un interpolateur RBF
        rbf_interpolator = RBFInterpolator(valid_indices, valid_values, kernel='linear')  # Ou essayez 'thin_plate'

        # Interpoler les valeurs aux positions des trous
        interpolated_values = rbf_interpolator(hole_indices)

        print("fill_holes_simple - 5")
        # Remplir les trous avec les valeurs interpolées
        mns_filled = mns.copy()
        for (i, j), val in zip(hole_indices, interpolated_values):
            if not np.isnan(val):  # Ignorer les NaN restants
                mns_filled[i, j] = val

        # Sauvegarde du résultat dans un nouveau fichier
        out_meta = src.meta.copy()
        out_meta.update({
            "dtype": 'float32'  # Type de données pour les valeurs interpolées
        })

        print("fill_holes_simple - 6")
        with rasterio.open(chemMNS_filled, 'w', **out_meta) as dst:
            dst.write(mns_filled, 1)

####################################################################################################
def fill_holes_simple_NEW(chemMNS_IN, no_data_int, no_data_ext, chemMNS_filled):
    with rasterio.open(chemMNS_IN) as src:
        mns = src.read(1)  # Lecture de la première bande dans un tableau NumPy
        #print('src.read')
        # Masque uniquement des pixels no_data_int pour les trous à combler
        mask_invalid = (mns == no_data_int)
        print('invalid identifiés')
        # Identifier les coordonnées des pixels valides (hors no_data_int) et des trous (no_data_int)
        valid_indices = np.argwhere(~mask_invalid & (mns != no_data_ext))  # Coordonnées des pixels valides (non NoData)
        hole_indices = np.argwhere(mask_invalid)                           # Coordonnées des trous (no_data_int uniquement)
        
        # Extraire les valeurs des pixels valides (hors no_data_int et no_data_ext)
        valid_values = mns[valid_indices[:, 0], valid_indices[:, 1]]

        print("fill_holes_simple - interpolation")
        # Interpolation linéaire pour combler les trous (no_data_int uniquement)
        interpolated_values = griddata(
            valid_indices,      # Points valides pour interpolation
            valid_values,       # Valeurs aux points valides
            hole_indices,       # Points à interpoler (trous no_data_int)
            method='linear'     # Interpolation linéaire
        )

        print("fill_holes_simple - fill")
        # Remplir les trous avec les valeurs interpolées sans boucle
        # Filtrer les indices où les valeurs interpolées ne sont pas NaN
        valid_hole_indices = ~np.isnan(interpolated_values)
        mns_filled = mns.copy()
        mns_filled[hole_indices[valid_hole_indices, 0], hole_indices[valid_hole_indices, 1]] = interpolated_values[valid_hole_indices]

        # Sauvegarde du résultat dans un nouveau fichier
        out_meta = src.meta.copy()
        out_meta.update({
            "dtype": 'float32'  # Type de données pour les valeurs interpolées
        })

        with rasterio.open(chemMNS_filled, 'w', **out_meta) as dst:
            dst.write(mns_filled, 1)

####################################################################################################
def fill_holes_simple(chemMNS_IN, no_data_int, no_data_ext, chemMNS_filled):
    with rasterio.open(chemMNS_IN) as src:
        mns = src.read(1)  # Lecture de la première bande dans un tableau NumPy
        #print('src.read')

        # Masque pour les pixels `no_data_int` uniquement
        mask_invalid = (mns == no_data_int)
        #print('invalid identifiés')
        
        # Coordonnées des pixels valides et trous
        valid_indices = np.argwhere(~mask_invalid & (mns != no_data_ext))
        hole_indices = np.argwhere(mask_invalid)
        valid_values = mns[valid_indices[:, 0], valid_indices[:, 1]]

        if hole_indices.size == 0:
            #print("Aucun trou détecté, aucune interpolation nécessaire.")
            mns_filled = mns.copy()
        else:
            # Utiliser LinearNDInterpolator
            interpolator = LinearNDInterpolator(valid_indices, valid_values)
            interpolated_values = interpolator(hole_indices)
            print("fill_holes_simple - interpolation")
            # Remplir les trous avec les valeurs interpolées
            mns_filled = mns.copy()
            valid_hole_indices = ~np.isnan(interpolated_values)
            mns_filled[hole_indices[valid_hole_indices, 0], hole_indices[valid_hole_indices, 1]] = interpolated_values[valid_hole_indices]
            print("fill_holes_simple - fill")

        # Sauvegarde du résultat
        out_meta = src.meta.copy()
        out_meta.update({"dtype": 'float32'})
        with rasterio.open(chemMNS_filled, 'w', **out_meta) as dst:
            dst.write(mns_filled, 1)

####################################################################################################
def Remplacer_no_data_max(chem_mns_nodata, chem_mns_nodata_max, no_data_ext, no_data_max):
    # Ouvrir l'image en mode lecture
    with rasterio.open(chem_mns_nodata) as src:
        # Lire les métadonnées et les données de l'image
        profile = src.profile
        data = src.read(1)  # Lire uniquement la première bande

        # Vérifier et remplacer la valeur no_data_ext par no_data_max
        data[data == no_data_ext] = no_data_max

        # Mettre à jour la valeur no_data dans les métadonnées
        profile.update(nodata=no_data_max)

        # Sauvegarder l'image modifiée avec le même géoréférencement
        with rasterio.open(chem_mns_nodata_max, 'w', **profile) as dst:
            dst.write(data, 1)

####################################################################################################
def Set_nodata_extern_to_final_GEMO_DTM(chemMNT_OUT_tmp,chemMNS_SousEch_tmp,no_data_ext,chemMNT_OUT):
    
    with rasterio.open(chemMNT_OUT_tmp) as src_mnt, rasterio.open(chemMNS_SousEch_tmp) as src_mns:   

        assert src_mnt.shape == src_mns.shape, "Les deux images MNT_OUT_tmp & MNS_SousEch_tmp doivent avoir les mêmes dimensions."

        # Lire les bandes dans des tableaux NumPy
        mnt_tmp = src_mnt.read(1) 
        mns_in = src_mns.read(1)           

        # Appliquer la condition pour générer le masque de sortie
        mnt_out = np.where(mns_in == no_data_ext, no_data_ext, mnt_tmp).astype(np.float32)

        # Préparer les métadonnées de l'image de sortie
        out_meta = src_mnt.meta.copy()
        out_meta.update({
            "dtype": 'float32',  # Type de données pour le masque de sortie
            "count": 1,        # Nombre de bandes
            "compress": 'lzw'  # Compression optionnelle
        })

        # Écrire l'image de sortie
        with rasterio.open(chemMNT_OUT, 'w', **out_meta) as dst:
            dst.write(mnt_out, 1)  # Écrire dans la première bande

####################################################################################################
def Set_nodata_extern_MNS_to_nodata_intern_mask(chemMASQUE_4gemo, chemMNS_IN, no_data_ext, no_data_interne_mask, chemMASQUE_nodata):
    # Charger les deux images en lecture
    with rasterio.open(chemMASQUE_4gemo) as src_masque, rasterio.open(chemMNS_IN) as src_mns:
        # Vérifier que les dimensions sont identiques
        assert src_masque.shape == src_mns.shape, "Les deux images doivent avoir les mêmes dimensions."
        
        # Lire les bandes dans des tableaux NumPy
        masque_4gemo = src_masque.read(1)  # Première bande de chemMASQUE_4gemo
        mns_in = src_mns.read(1)           # Première bande de chemMNS_IN

        # Appliquer la condition pour générer le masque de sortie
        masque_nodata = np.where(mns_in == no_data_ext, no_data_interne_mask, masque_4gemo).astype(np.uint8)

        # Préparer les métadonnées de l'image de sortie
        out_meta = src_masque.meta.copy()
        out_meta.update({
            "dtype": 'uint8',  # Type de données pour le masque de sortie
            "count": 1,        # Nombre de bandes
            "compress": 'lzw'  # Compression optionnelle
        })

        # Écrire l'image de sortie
        with rasterio.open(chemMASQUE_nodata, 'w', **out_meta) as dst:
            dst.write(masque_nodata, 1)  # Écrire dans la première bande

####################################################################################################
def Set_groundval_mask_to_0(chemMASQUE, groundval, chemMASQUE_4gemo):
    # Ouvrir l'image d'entrée en mode lecture
    with rasterio.open(chemMASQUE) as src:
        # Lire les données de la première bande dans un tableau NumPy
        img_array = src.read(1)  # Lire la première bande uniquement

        # Appliquer la condition : si le pixel est égal à groundval, mettre 0, sinon 255
        masque_binaire = np.where(img_array == groundval, 0, 255).astype(np.uint8)

        # Paramètres pour le fichier de sortie
        out_meta = src.meta.copy()
        out_meta.update({
            "dtype": 'uint8',  # Type de données pour les pixels en sortie
            "count": 1,        # Nombre de bandes
            "compress": 'lzw'  # Compression optionnelle
        })

        # Écrire l'image de sortie avec Rasterio
        with rasterio.open(chemMASQUE_4gemo, 'w', **out_meta) as dst:
            dst.write(masque_binaire, 1)

####################################################################################################
def parse_arguments():

    # Création du parseur d'arguments avec une description et un épilogue pour l'exemple de commande
    parser = argparse.ArgumentParser(
        description='GEMAUT - Génération de Modèles Automatiques de Terrain',
        epilog="""EXEMPLE DE LIGNE DE COMMANDE:
        script_gemaut --mns /chem/vers/MNS_in.tif --out /chem/vers/MNT.tif --reso 4 --cpu 24 --RepTra /chem/vers/RepTra [--sigma 0.5] [--regul 0.01] [--tile 300] [--pad 120] [--norme hubertukey] [--nodata_ext -32768] [--nodata_int -32767] [--init /chem/vers/MNS_in.tif] [--masque /chem/vers/MASQUE_GEMO.tif] [--groundval 0] [--clean]
        
        \n IMPORTANT
        Le MNS doit avoir des valeurs de no_data différentes pour les bords de chantier [no_data_ext] et les trous à l'intérieur du chantier [no_data_int] là où la corrélation a échoué par exemple

    """,
        formatter_class=argparse.RawTextHelpFormatter
    )


    # Définition des arguments du programme
    parser.add_argument("--mns", type=str, required=True, help="input DSM")
    parser.add_argument("--out", type=str, required=True, help="output DTM")
    parser.add_argument("--reso", type=float, required=True, default=4, help="resolution du MNT en sortie")
    parser.add_argument("--cpu", type=int, required=True, help="nombre de CPUs à utiliser dans le traitement")
    parser.add_argument("--RepTra", type=str, required=True, help="repertoire de Travail")
    # 
    parser.add_argument("--masque", type=str, help="input ground/above-ground MASK")
    parser.add_argument("--groundval", default=0, type=int, help="valeur de masque pour le SOL (obligatoire si --masque est renseigné)")
    parser.add_argument("--init", type=str, help="initialisation [par défaut le MNS]")
    parser.add_argument("--nodata_ext", type=int, default=-32768, help="Valeur du no_data sur les bords de chantier")
    parser.add_argument("--nodata_int", type=int, default=-32767, help="Valeur du no_data pour les trous à l'intérieur du chantier")
    parser.add_argument("--sigma", type=float, default=0.5, help="sigma / précision du Z MNS")
    parser.add_argument("--regul", type=float, default=0.01, help="regul / rigidité de la nappe")
    parser.add_argument("--tile", type=int, default=300, help="taille de la tuile")
    parser.add_argument("--pad", type=int, default=120, help="recouvrement entre tuiles")
    parser.add_argument("--norme", type=str, default="hubertukey", help="choix entre les normes /tukey/huber/hubertukey/L1/L2")
    parser.add_argument("--clean", action='store_true', help="pour supprimer les fichiers temporaires à la fin du traitement")
    
    # Parsing des arguments
    args = parser.parse_args(sys.argv[1:])

    # Validation conditionnelle
    if args.masque and args.groundval is None:
        parser.error("--groundval est obligatoire si --masque est renseigné.")

    return args

####################################################################################################
def main():

    try:

        args = parse_arguments()
        chemMNS_IN=args.mns 
        chemMNT_OUT=args.out
        chemMASQUE=args.masque
        RepTravail=args.RepTra
        groundval=args.groundval
        reso_travail=args.reso
        fsigma=args.sigma
        flambda=args.regul
        iTailleparcelle=args.tile
        iTailleRecouvrement=args.pad
        iNbreCPU=args.cpu
        norme=args.norme
        no_data_ext=args.nodata_ext
        no_data_int=args.nodata_int     
        no_data_interne_mask=11 
        no_data_max=32768
        radius_saga=100 
        tile_saga=100
        pente=15
        #taille_voisinage=5
        #K=2
        #percentile=5
        #taille_dallage=20
        #seuil_diff=15

        # Ajouter un gestionnaire pour enregistrer dans un fichier
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_file_path = os.path.join(os.path.dirname(chemMNT_OUT), f"log_{timestamp}.txt")  
        logger.remove()
        logger.add(log_file_path, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
        start_time = time.time()
        start_time_str = time.strftime("%d-%m-%Y %H:%M:%S", time.localtime(start_time))
        logger.info(f"Programme démarré à : {start_time_str}")

        ### 
        RepTravail_tmp=os.path.join(RepTravail,"tmp")
        if not os.path.isdir(RepTravail): os.mkdir(RepTravail)
        if not os.path.isdir(RepTravail_tmp): os.mkdir(RepTravail_tmp)

        ###        
        chemMNS=os.path.join(RepTravail_tmp,'MNS_sans_trou.tif')
        chemMNS4SAGA=os.path.join(RepTravail_tmp,'MNS4SAGA_nodata_max.tif')
        chemMNS_SousEch_tmp= os.path.join(RepTravail_tmp,'MNS_SousEch_tmp.tif')
        chemMASQUE_4gemo=os.path.join(RepTravail_tmp,'MASQUE_4gemo.tif')
        chemMASQUE_nodata=os.path.join(RepTravail_tmp,'MASQUE_nodata.tif')
        chemMASQUE_SousEch=os.path.join(RepTravail_tmp,'MASQUE_SousEch.tif')
        chemMNT_OUT_tmp=os.path.join(RepTravail_tmp,'OUT_MNT_tmp.tif')
        chemINIT_SousEch=os.path.join(RepTravail_tmp,'INIT.tif')
        Chem_RepTra_SAGA=os.path.join(RepTravail_tmp,'RepTra_SAGA')

        #
        if not os.path.isdir(Chem_RepTra_SAGA): 
            os.mkdir(Chem_RepTra_SAGA)
        else:
            shutil.rmtree(Chem_RepTra_SAGA)
            os.mkdir(Chem_RepTra_SAGA)

        logger.info("Remplissage des trous dans MNS.")
        fill_holes_simple(chemMNS_IN, no_data_int, no_data_ext, chemMNS)
        
        #
        logger.info("Remplacement des valeurs NoData max dans MNS.")
        Remplacer_no_data_max(chemMNS, chemMNS4SAGA, no_data_ext, no_data_max)

        #
        if args.masque is None:
            #
            logger.info("Le masque n'a pas été fourni. Calcul à partir du MNS avec SAGA.")
            chemMASQUE=os.path.join(RepTravail,'MASQUE_compute.tif')
            if os.path.isfile(chemMASQUE):
                os.remove(chemMASQUE)  # Supprimer le fichier
                logger.info("Le fichier {chemMASQUE} a été supprimé: il va être recalculé")
                #print(f"Le fichier {chemMASQUE} a été supprimé: il va être recalculé")
            else:
                logger.info("Le fichier {chemMASQUE} n'existe pas: il va être recalculé")
                #print(f"Le fichier {chemMASQUE} n'existe pas: il va être recalculé")

            # Appeler le script en utilisant subprocess
            try:
                main_saga_ground_extraction(chemMNS4SAGA,chemMASQUE,Chem_RepTra_SAGA,iNbreCPU,radius_saga,tile_saga,no_data_max,pente)
            except subprocess.CalledProcessError as e:
                logger.error(f"Erreur lors de l'exécution du script SAGA: {e}")
                
        else:
            chemMASQUE=args.masque
        
        # On utilise foreval pour être dans la convention de GEMO: SOL = 0 / SURSOL =255
        logger.info("Etiquetage et remplissage des valeurs NoData.")
        Set_groundval_mask_to_0(chemMASQUE, groundval, chemMASQUE_4gemo)

        # Affectation d'une valeur spécifique pour gérer les bords de chantier = 11 (no_data_interne_mask)
        logger.info("Gestion des valeurs NoData externes et internes.")
        Set_nodata_extern_MNS_to_nodata_intern_mask(chemMASQUE_4gemo, chemMNS_IN, no_data_ext, no_data_interne_mask, chemMASQUE_nodata)

        #
        logger.info(f"Sous-échantillonnage à la résolution de {reso_travail} mètres.")        
        ## SousEch de MNS et MASQUE 
        cmd_SousEch_MNS="gdalwarp -tr %2.10f %2.10f -srcnodata %d -dstnodata %d %s %s -overwrite" %(reso_travail,reso_travail,no_data_ext,no_data_ext,chemMNS,chemMNS_SousEch_tmp)
        logger.info(f"Commande GDAL: {cmd_SousEch_MNS}")
        run_task_sans_SORTIEMESSAGE(cmd_SousEch_MNS)
        
        if not os.path.exists(chemMNS_SousEch_tmp):
            raise FileNotFoundError(f"Le fichier sous-échantillonné n'a pas été créé : {chemMNS_SousEch_tmp}")
        
        ## SousEch de MASQUE
        cmd_SousEch_MASQUE="gdalwarp -tr %2.10f %2.10f -srcnodata %d -dstnodata %d %s %s -ot Byte -overwrite " %(reso_travail,reso_travail,no_data_interne_mask,no_data_interne_mask,chemMASQUE_nodata,chemMASQUE_SousEch)
        logger.info(f"Commande GDAL: {cmd_SousEch_MASQUE}")
        run_task_sans_SORTIEMESSAGE(cmd_SousEch_MASQUE)
        
        if not os.path.exists(chemMASQUE_SousEch):
            raise FileNotFoundError(f"Le fichier masque sous-échantillonné n'a pas été créé : {chemMASQUE_SousEch}")
        
        chemINIT = chemMNS if args.init is None else args.init
        logger.info(f"Initialisation avec : {chemINIT}.")
        
        # SousEch de INIT
        cmd_SousEch_INIT="gdalwarp -tr %2.10f %2.10f -srcnodata %d -dstnodata %d %s %s -overwrite " %(reso_travail,reso_travail,no_data_ext,no_data_ext,chemINIT,chemINIT_SousEch)
        logger.info(f"Commande GDAL: {cmd_SousEch_INIT}")
        run_task_sans_SORTIEMESSAGE(cmd_SousEch_INIT)
        
        if not os.path.exists(chemINIT_SousEch):
            raise FileNotFoundError(f"Le fichier d'initialisation sous-échantillonné n'a pas été créé : {chemINIT_SousEch}")
        
        logger.info("Calcul du nombre de dalles.")       
        NbreDalleX, NbreDalleY = GetNbreDalleXDalleY(chemMNS_SousEch_tmp,iTailleparcelle,iTailleRecouvrement)
        print('-------------------------------- ', NbreDalleX, NbreDalleY)
        print(f"Nombre de dalles - TEST : {NbreDalleX}x{NbreDalleY}")
        logger.info(f"Nombre de dalles - TEST : {NbreDalleX}x{NbreDalleY}")
                
        logger.info("Découpage des dalles pour chantier GEMO.")  
        taille_dalle=(iTailleparcelle,iTailleparcelle)
        try:
            Decoupe_chantier(chemMNS_SousEch_tmp, chemMASQUE_SousEch, chemINIT_SousEch, taille_dalle, iTailleRecouvrement, no_data_ext, RepTravail_tmp, iNbreCPU)
            
            # Vérifier que les dalles ont bien été créées
            dalles_manquantes = []
            for x in range(NbreDalleX):
                for y in range(NbreDalleY):
                    RepDalleXY = os.path.join(RepTravail_tmp, f"Dalle_{x}_{y}")
                    if not os.path.exists(RepDalleXY):
                        dalles_manquantes.append(f"Dalle_{x}_{y}")
                    else:
                        files = os.listdir(RepDalleXY)
                        logger.debug(f"Contenu de Dalle_{x}_{y}: {files}")
            
            if dalles_manquantes:
                raise RuntimeError(f"Les dalles suivantes n'ont pas été créées : {', '.join(dalles_manquantes)}")
            
        except Exception as e:
            logger.error(f"Erreur lors du découpage des dalles : {str(e)}")
            raise

        logger.info("Exécution parallèle de GEMO.")
        RunGemoEnParallel(RepTravail_tmp, NbreDalleX, NbreDalleY, fsigma, flambda, norme, no_data_ext, iNbreCPU)

        logger.info("Raboutage final avec Rasterio.")
        Raboutage(RepTravail_tmp,NbreDalleX,NbreDalleY,chemMNT_OUT_tmp)    

        Set_nodata_extern_to_final_GEMO_DTM(chemMNT_OUT_tmp,chemMNS_SousEch_tmp,no_data_ext,chemMNT_OUT)

        # rajouter une option DEBUG
        # suppression des fichiers temporaires 
        if args.clean:
            shutil.rmtree(RepTravail_tmp)
            logger.info("Nettoyage des fichiers temporaires effectué.")
                
        # Arrêter le chronomètre et calculer le temps écoulé
        end_time = time.time()
        elapsed_time = end_time - start_time  # Temps écoulé en secondes
        
        #Convertir le temps écoulé en heures, minutes, secondes
        formatted_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

        # Afficher le temps total de traitement
        logger.info(f"Temps total de traitement: {formatted_time}")       
		
        logger.info("END")

#==================================================================================================
# Gestion des exceptions
#==================================================================================================
    except (RuntimeError, TypeError, NameError) as e:
        logger.error(f"Erreur: {e}")
        print("ERREUR:", e)

####################################################################################################
if __name__ == "__main__":
    main()
