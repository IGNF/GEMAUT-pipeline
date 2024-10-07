#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os, time, shutil
import subprocess
import argparse
import rasterio
from rasterio.windows import Window
import numpy as np
from multiprocessing import Pool
from tqdm import tqdm
import signal
import time

#==================================================================================================
# Usage
#==================================================================================================
# def Usage():
    # print """
# USAGE :
# Version du 08/12/2020


# Génération de MNT avec GEMAUT(Génération et Modélisation AUtomatique du Terrain)

### ./script_run_gemaut_chantier_complet_pour_serveur  
            ### -in_dsm /chemin/vers/MNS.tif            ### /chemin/vers/MNS.tif 
            ### -init /chemin/vers/initialisation.tif   ### /chemin/vers/initialisation.tif
            ### -in_mask /chemin/vers/MASQUE.tif        ### /chemin/vers/MASQUE.tif
            ### -out chemin/vers/repertoire/OUT_GEMAUT  ### /chemin/vers/repertoire/OUT
            ### -downsampling 4 [en mètres]            	### Résolution de travail
            ### -sigma 0.5                             	### coefficient_sigma
            ### -regul 0.01                         	### coefficient_lambda
            ### -tile 300                             	### taille_dalle_decoupage_chantier
            ### -pad 120                            	### recouv_dalle_chantier
            ### -cpu 20                              	### nombre_processeurs_a_utiliser
            ### -norme hubertukey                    	### norme à utiliser
            
### EXEMPLE DE LIGNE DE COMMANDE: ./script_run_gemaut_chantier_complet_pour_serveur.py -downsampling 2 -sigma 0.5 -regul 0.01 -tile  300 -pad 120 -cpu 56 -norme HuberTukey -in_dsm MNS_in.tif -init MNS_in.tif -in_mask MASQUE_GEMO.tif -out REP_OUT
            
#
# """     

cmd_XinG='_XinG'
cmdxingng='xingng'
#cmdxingng_chem_complet='/Volumes/ALI_Serveur/OUTILS_IGNE/OUTILS_EIDS/bin_linux/xingng'
cmdxingng_chem_complet='/Volumes/ALI_Serveur/DEPLOIEMENT/bin_linux/xingng' 
cmd_blending_otb='/home/OTB/OTB-7.4.0-Linux64/bin/otbcli_Mosaic'        

#################################################################################################### 
def init_worker():
	signal.signal(signal.SIGINT, signal.SIG_IGN)

################################################################################################################################
def cmd_docker_saga_1_dalle(chem_rep_montage,chem_RELATIF_IN,chem_RELATIF_OUT,pente):
    # Définir les chemins des fichiers et les paramètres
    #"/data/PO_MNS_LA93.tif"
    chem_dsm_4_docker = os.path.join('/data',chem_RELATIF_IN)
    #"/data/RepTra"
    chem_RepTra_4_docker = os.path.join('/data',chem_RELATIF_OUT)
    # slope = 15
    
    # Construire la commande Docker
    command_docker_extract_ground_saga = f"docker run --rm -v {chem_rep_montage}:/data extract_ground_points --dsm {chem_dsm_4_docker} --RepTra {chem_RepTra_4_docker} --slope {pente}"
    #print(f"{command_docker_extract_ground_saga}")
    
    return command_docker_extract_ground_saga

    # # Exécuter la commande Docker
    # exit_code = os.system(command_docker_extract_ground_saga)
    
    # # Vérifier le code de sortie
    # if exit_code == 0:
    #     print("Command executed successfully")
    # else:
    #     print(f"Command failed with exit code {exit_code}")

################################################################################################################################
def run_docker_saga_par_dalle_parallel(RepIN,RepOUT,chem_pente_par_dallle,taille_dallage,iNbreCPU):

    # Trouver la racine commune - qui correspond aussi au point de montage
    chem_rep_montage = os.path.commonpath([RepIN, RepOUT])

    # Chemin relatif de RepIN et RepOUT par rapport à RACINE
    RepIN_relatif = os.path.relpath(RepIN, chem_rep_montage)
    RepOUT_relatif = os.path.relpath(RepOUT, chem_rep_montage)

    liste_pixel_coords=[]
    liste_images=[]
    liste_rep_out=[]

    for root, dirs, files in os.walk(RepIN):
        for f in files:
            #
            liste_tmp=f.split('_')
            ligne_tmp=int(liste_tmp[1])
            colonne_tmp=int(liste_tmp[2].split('.')[0])
            # print(ligne_tmp,' - ',colonne_tmp)
            ligne=(ligne_tmp-1)*taille_dallage
            colonne=(colonne_tmp-1)*taille_dallage
            #
            pixel_coords=[ligne,colonne]
            liste_pixel_coords.append(pixel_coords)
            #
            # liste_images.append(os.path.join(root,f))
            # print(os.path.join(os.path.relpath(root,chem_rep_montage),f)
            liste_images.append(os.path.join(os.path.relpath(root,chem_rep_montage),f))

            # préparer / créer le dossier de sortie et l'ajouter à la liste
            chem_RepTra_SAGA_OUT_1_dalle=os.path.join(RepOUT,f[:-4])
            if not os.path.isdir(chem_RepTra_SAGA_OUT_1_dalle): os.mkdir(chem_RepTra_SAGA_OUT_1_dalle)
            chem_RepTra_SAGA_OUT_1_dalle_RELATIF=os.path.join(RepOUT_relatif,f[:-4])
            liste_rep_out.append(chem_RepTra_SAGA_OUT_1_dalle_RELATIF)

    tasks = []

    # Ouverture de l'image une seule fois
    with rasterio.open(chem_pente_par_dallle) as dataset:
        band_data = dataset.read(1)
        #
        for (row, col), chem_img, chem_rep_out in zip(liste_pixel_coords, liste_images, liste_rep_out):
            pente_local = band_data[row, col]
            # print(cmd_docker_saga_1_dalle(chem_rep_montage,chem_img,chem_rep_out,pente_local))
            tasks.append(cmd_docker_saga_1_dalle(chem_rep_montage,chem_img,chem_rep_out,pente_local))

            #chem_ground=os.path.join(RepOUT,os.path.basename(os.path.splitext(chem_img)[0]) + '_ground.sdat')
            #chem_non_ground=os.path.join(RepOUT,os.path.basename(os.path.splitext(chem_img)[0]) + '_non_ground.sdat')
            
	# Initialize the pool 
    with Pool(processes=iNbreCPU, initializer=init_worker) as pool:
        results = list(tqdm(pool.imap_unordered(os.system, tasks), total=len(tasks), desc="Lancement de SAGA en parallèle"))

    return

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

################################################################################################################################
def Calcule_pente_et_filtre(chem_mns,RepTra_tmp,chem_pente_filtree,taille,K,percentile,seuil_diff):

    chem_pente=os.path.join(RepTra_tmp,'pente.tif')
    chem_pente_smooth=os.path.join(RepTra_tmp,'pente_smooth.tif')
    chem_diff_pente_smooth=os.path.join(RepTra_tmp,'diff_pente_smooth.tif')

    # xingng -i MNS.tif -Xp -o pente.tif
    cmd=f"xingng -i {chem_mns} -Xp -o {chem_pente} -n0 > /dev/null 2>&1 "
    # print(cmd)
    os.system(cmd)

    # on fait du nettoyage dans les bâtiments avec FN_5x5_Q_5
    # xingng -i ./pente.tif -FN:5:5:2:Q:5 -o pente_FN_5x5_Q_5.tif
    cmd=f"xingng -i {chem_pente} -FN:{taille}:{taille}:{K}:Q:{percentile} -o {chem_pente_smooth} -n0 > /dev/null 2>&1 "
    print(cmd)
    os.system(cmd)

    cmd=f"xingng -i {chem_pente} {chem_pente_smooth} -X- -o {chem_diff_pente_smooth} -n0 > /dev/null 2>&1 "
    os.system(cmd)

    # xingng -i pente.tif pente_CROP_FN_5x5_Q_5.tif diff.tif -e'I3.1>15?I2.1:I1.1' -o pente_filtree.tif
    cmd=f"xingng -i {chem_pente} {chem_pente_smooth} {chem_diff_pente_smooth} -e'I3.1>{seuil_diff}?I2.1:I1.1' -o {chem_pente_filtree} -n0 > /dev/null 2>&1 " 
    os.system(cmd)

    return

############################################################################################################
def compute_ground_mask_parallel(chem_mns,chem_out_final,RepTra,taille_voisinage,K,percentile,taille_dallage,seuil_diff,iNbreCPU):
    
    RepTra_tmp=os.path.join(RepTra,"tmp")
    if not os.path.isdir(RepTra): os.mkdir(RepTra)
    if not os.path.isdir(RepTra_tmp): os.mkdir(RepTra_tmp)

    #
    chem_pente_filtree=os.path.join(RepTra_tmp,'pente_filtree.tif')
    Calcule_pente_et_filtre(chem_mns,RepTra_tmp,chem_pente_filtree,taille_voisinage,K,percentile,seuil_diff)

    #
    chem_pente_par_dallle=os.path.join(RepTra_tmp,'pente_par_dallle.tif')
    dallage_pente(chem_pente_filtree,chem_pente_par_dallle,taille_dallage)

    # #
    # # Découper suivant des dalles de taille_dallage
    RepTra_DALLAGE_tmp=os.path.join(RepTra_tmp,"DALLAGE")
    if not os.path.isdir(RepTra_DALLAGE_tmp): os.mkdir(RepTra_DALLAGE_tmp)
        
    #
    chem_DALLAGE_out=os.path.join(RepTra_DALLAGE_tmp,'DALLAGE')
    cmd=f"xingng -i {chem_mns} -Di:N:20:20 -o {chem_DALLAGE_out} -n0 > /dev/null 2>&1"
    os.system(cmd)
        
    #
    RepTra_OUT_SAGA_tmp=os.path.join(RepTra_tmp,"OUT_SAGA_tmp")
    if not os.path.isdir(RepTra_OUT_SAGA_tmp): os.mkdir(RepTra_OUT_SAGA_tmp)
    run_docker_saga_par_dalle_parallel(RepTra_DALLAGE_tmp,RepTra_OUT_SAGA_tmp,chem_pente_par_dallle,taille_dallage,iNbreCPU)

    #
    for root, dirs, files in os.walk(RepTra_OUT_SAGA_tmp):
        for f in files:
            if f.startswith('ground') and f.endswith('.sdat'):
                chem_in=os.path.join(root,f)
                chem_out=f"{chem_in[:-5]}.tif"
                cmd=f"gdal_translate {chem_in} {chem_out}"
                os.system(cmd)

    # cmd_ass=f"xingng -i {}  -a -o {os.path.join(chem_out_final,expression)} -n0 > /dev/null 2>&1 " 
    expression="*/ground.tif" 
    chem_assemblage=os.path.join(RepTra_tmp,'ASS.tif')
    cmd_ass_final=f"xingng -i {os.path.join(RepTra_OUT_SAGA_tmp,expression)}  -a -o {chem_assemblage} -n0 > /dev/null 2>&1 " 
    print(cmd_ass_final)
    os.system(cmd_ass_final) 

    cmd_final=f"xingng -i {chem_assemblage} -e'I1.1==-99999?255:0' -o {chem_out_final} -tuc -n0 > /dev/null 2>&1 "
    print(cmd_final)
    os.system(cmd_final) 

    return

##################################################################################################################
def Raboutage_OTB_BUG(RepTravail_tmp,NbreDalleX,NbreDalleY,chemMNT_OUT):
    #### Assemblage final - avec OTB buggué
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
def Raboutage(RepTravail_tmp,NbreDalleX,NbreDalleY,chemMNT_OUT):

    #total_steps = (NbreDalleY * (NbreDalleX - 1)) + NbreDalleY + (NbreDalleY - 1) + 1
    total_steps = (NbreDalleY * (NbreDalleX - 1)) + 2 * NbreDalleY
    with tqdm(total=total_steps, desc="Progression globale", unit="étape") as pbar:
        
        ####################################################################################################################################################
        ####################################################################################################################################################                
        ## on assemble tout d'abord ligne par ligne       #####################################################################################################
        ####################################################################################################################################################
        ####################################################################################################################################################
        
        ####################################################################################################################################################        
        ## on raboute tout d'abord 2 dalles côte à côté (en X)       #########################################################################################
        ####################################################################################################################################################    
        
        for y in range(NbreDalleY):
            for x in range(NbreDalleX-1):
                ## Nom de la dalle courante    
                chem_MNT_GEMAUT_OUT_dalle_xy=os.path.join(RepTravail_tmp,"Dalle_%s_%s"%(x,y),"Out_MNT_%s_%s.tif"%(x,y))
                chem_MNT_GEMAUT_OUT_dalle_xy_droite=os.path.join(RepTravail_tmp,"Dalle_%s_%s"%(x+1,y),"Out_MNT_%s_%s.tif"%(x+1,y))                
                ## IMAGE GAUCHE / IMAGE DROITE <> DALLE_0_0 / DALLE_1_0 !
                cmd_1="%s -i %s %s -X- -o %s -n0 >> /dev/null 2>&1 " %(cmdxingng,chem_MNT_GEMAUT_OUT_dalle_xy,chem_MNT_GEMAUT_OUT_dalle_xy_droite, os.path.join(RepTravail_tmp,'diff_tmp.tif'))
                # à décommenter # print(cmd_1)
                os.system(cmd_1)

                cmd_2="%s -i %s -e'C/NC' -o  %s -tf -n0 >> /dev/null 2>&1" %(cmdxingng,os.path.join(RepTravail_tmp,'diff_tmp.tif'),os.path.join(RepTravail_tmp,'poids_HG_HD_pour_HD.tif'))
                # print(cmd_2)
                os.system(cmd_2)
                
                cmd_3="%s -i %s -e'1-I1' -o  %s -n0 >> /dev/null 2>&1" %(cmdxingng,os.path.join(RepTravail_tmp,'poids_HG_HD_pour_HD.tif'),os.path.join(RepTravail_tmp,'poids_HG_HD_pour_HG.tif'))
                # print(cmd_3)
                os.system(cmd_3)
                
                liste_info_tmp=GetInfo(cmdxingng, os.path.join(RepTravail_tmp,'poids_HG_HD_pour_HD.tif'))

                cmd_final="%s -i %s %s %s %s -e'I1*I2+I3*I4' -o %s -cg:%s:%s:%s:%s -n0 >> /dev/null 2>&1" %(cmdxingng,chem_MNT_GEMAUT_OUT_dalle_xy,
                                                                                    os.path.join(RepTravail_tmp,'poids_HG_HD_pour_HG.tif'),
                                                                                    chem_MNT_GEMAUT_OUT_dalle_xy_droite, 
                                                                                    os.path.join(RepTravail_tmp,'poids_HG_HD_pour_HD.tif'),
                                                                                    os.path.join(RepTravail_tmp,'reconstruction_dalle_%s_%s_%s.tif' %(x,x+1,y)),
                                                                                    liste_info_tmp[3],
                                                                                    liste_info_tmp[4],
                                                                                    liste_info_tmp[5],
                                                                                    liste_info_tmp[6])
                                                                                                                                                                    
                # print(cmd_final)
                pbar.update(1)
                os.system(cmd_final)

        ####################################################################################################################################################        
        ## on raboute toutes les dalles sur une même rangée        #########################################################################################
        ####################################################################################################################################################
                
        ## on réassemble tout    
        for y in range(NbreDalleY):
            
            ### initialisation ligne de commande
            cmd_assemblage_final_par_ligne="%s -i " %cmdxingng
            
            for x in range(NbreDalleX):
                cmd_assemblage_final_par_ligne=cmd_assemblage_final_par_ligne+" "+os.path.join(RepTravail_tmp,"Dalle_%s_%s"%(x,y),"Out_MNT_%s_%s.tif"%(x,y))
                                
            for x in range(NbreDalleX-1):
                cmd_assemblage_final_par_ligne=cmd_assemblage_final_par_ligne+" "+os.path.join(RepTravail_tmp,'reconstruction_dalle_%s_%s_%s.tif' %(x,x+1,y))
                
            #
            chem_final_tmp=os.path.join(RepTravail_tmp,'reconstruction_dalle_%s.tif' %y) 
            str_tmp=" -a -o %s -n:" %chem_final_tmp
            cmd_assemblage_final_par_ligne+=str_tmp
            
            # print(cmd_assemblage_final_par_ligne)
            pbar.update(1)
            os.system(cmd_assemblage_final_par_ligne)    
            
        ####################################################################################################################################################
        ####################################################################################################################################################                
        ## on assemble les rangées entre elles         #####################################################################################################
        ####################################################################################################################################################
        ####################################################################################################################################################
                    
        ## on réassemble tout    
        for y in range(NbreDalleY-1):
            
            chem_dalle_y=os.path.join(RepTravail_tmp,'reconstruction_dalle_%s.tif' %y)             
            chem_dalle_y_dessous=os.path.join(RepTravail_tmp,'reconstruction_dalle_%s.tif' %(y+1))
            
            cmd_1="%s -i %s %s -X- -o %s -n:" %(cmdxingng,chem_dalle_y,chem_dalle_y_dessous,os.path.join(RepTravail_tmp,'diff_tmp.tif'))
            # print(cmd_1)
            os.system(cmd_1)
            
            cmd_2="%s -i %s -e'L/NL' -o %s -tf -n:" %(cmdxingng,os.path.join(RepTravail_tmp,'diff_tmp.tif'),os.path.join(RepTravail_tmp,'poids_HG_BG_pour_BG.tif'))
            # print(cmd_2)
            os.system(cmd_2)
            
            cmd_3="%s -i %s -e'1-I1' -o %s -n:" %(cmdxingng,os.path.join(RepTravail_tmp,'poids_HG_BG_pour_BG.tif'),os.path.join(RepTravail_tmp,'poids_HG_BG_pour_HG.tif'))
            # print(cmd_3)
            os.system(cmd_3)            
            
            liste_info_tmp=GetInfo(cmdxingng, os.path.join(RepTravail_tmp,'poids_HG_BG_pour_BG.tif'))
            
            cmd_final="%s -i %s %s %s %s -e'I1*I2+I3*I4' -o %s -cg:%s:%s:%s:%s -n:" %(cmdxingng,chem_dalle_y,
                                                                            os.path.join(RepTravail_tmp,'poids_HG_BG_pour_HG.tif'),
                                                                            chem_dalle_y_dessous,os.path.join(RepTravail_tmp,'poids_HG_BG_pour_BG.tif'),
                                                                            os.path.join(RepTravail_tmp,
                                                                            'reconstruction_dalle_%s_%s.tif' %(y,y+1)),
                                                                            liste_info_tmp[3],
                                                                            liste_info_tmp[4],
                                                                            liste_info_tmp[5],
                                                                            liste_info_tmp[6])
            # print(cmd_final)
            pbar.update(1)
            os.system(cmd_final)
            
        ### initialisation ligne de commande
        cmd_assemblage_final="%s -i " %cmdxingng
            
        ## on réassemble tout    
        for y in range(NbreDalleY):
            chem_dalle_y=os.path.join(RepTravail_tmp,'reconstruction_dalle_%s.tif' %y)     
            cmd_assemblage_final=cmd_assemblage_final+" "+chem_dalle_y
            
        ## on réassemble tout    
        for y in range(NbreDalleY-1):
            cmd_assemblage_final=cmd_assemblage_final+" "+os.path.join(RepTravail_tmp,'reconstruction_dalle_%s_%s.tif' %(y,y+1))
        
        # en ARGUMENT DE LA FONCTION MAINTENANT...
        # chemMNT_OUT=os.path.join(RepTravail,"OUT_MNT_GEMAUT_final.tif")
        str_tmp=" -a -o %s -n:" %chemMNT_OUT
        cmd_assemblage_final+=str_tmp
            
        # print(cmd_assemblage_final)
        pbar.update(1)
        os.system(cmd_assemblage_final)  

##################################################################################################################
##################################################################################################################
def GetValue(listInfo,chaine):
    
    for l in listInfo:
        lig=l.strip()
        if lig.find(chaine) != -1:
            return lig.split()[-1]      

#################################################################################################### 
### 
def    GetNbLignes(cmdxingng, chemMNS):   
    
    optionGetNbLignes="-n:stdout | awk '/nombre de lignes/ {print $6}'"
    cmdGetNbLignes="%s -i %s %s"% (cmdxingng, chemMNS, optionGetNbLignes)
    os.system(cmdGetNbLignes)
    pipe=os.popen(cmdGetNbLignes)
    sNbLignes=pipe.readline().rstrip()
    pipe.close()
    return int(sNbLignes)

#################################################################################################### 
### 
def    GetNbColonnes(cmdxingng, chemMNS):   
    
    optionGetNbColonnes="-n:stdout | awk '/nombre de colonnes/ {print $6}'"
    cmdGetNbColonnes="%s -i %s %s"% (cmdxingng, chemMNS, optionGetNbColonnes)
    os.system(cmdGetNbColonnes)
    pipe=os.popen(cmdGetNbColonnes)    
    sNbColonnes=pipe.readline().rstrip()
    pipe.close()
    return int(sNbColonnes)

# def    GetNbLignes(chemMNS):   
    
    # cmdGetNbLignes="gdalinfo %s  | awk '/Size is/ {print $4}'" %chemMNS
    # os.system(cmdGetNbLignes)
    # pipe=os.popen(cmdGetNbLignes)
    # sNbLignes=pipe.readline().rstrip()
    # pipe.close()
    # return int(sNbLignes)
    
# def    GetNbColonnes(chemMNS):   
    
    # cmdGetNbColonnes="gdalinfo %s  | awk '/Size is/ {print $3}'" %chemMNS
    # os.system(cmdGetNbColonnes)
    # pipe=os.popen(cmdGetNbColonnes)
    # sNbColonnes=pipe.readline().rstrip()[:-1]
    # pipe.close()
    # return int(sNbColonnes)
    
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
      
############################################################################################################################         
def GetInfo(cmdxingng, chemMNS):
    ### récupérer les infos dans un flux
    cmdinfo="%s -i %s  -n:stdout 2>/dev/null " % (cmdxingng,chemMNS)
    # print('*** ',cmdinfo)
    pipe= os.popen(cmdinfo)
    listInfo = pipe.readlines()
    pipe.close()
    ### initialisation des variables
    PasX, PasY, projection, X_0, X_1, Y_0, Y_1 = 0, 0, 0, 0, 0, 0, 0 
    phasage="HG"
    ### récupération des données
    PasX=float(GetValue(listInfo,"pas en X"))
    PasY=float(GetValue(listInfo,"pas en Y"))
    X_0=float(GetValue(listInfo,"position en X (GAUCHE)"))
    Y_1=float(GetValue(listInfo,"position en Y (HAUT)"))
    X_1=float(GetValue(listInfo,"position en X (DROITE)"))
    Y_0=float(GetValue(listInfo,"position en Y (BAS)")) 
    NbreCol=float(GetValue(listInfo,"nombre de colonnes"))
    NbreLig=float(GetValue(listInfo,"nombre de lignes"))
    if GetValue(listInfo,"GTModelTypeGeoKey"): GModel=int(GetValue(listInfo,"GTModelTypeGeoKey"))      
    else: GModel=-1
    if GetValue(listInfo,"GTRasterTypeGeoKey"): GRaster=int(GetValue(listInfo,"GTRasterTypeGeoKey"))
    else: GRaster=-1
    if GetValue(listInfo,"code EPSG"): Projection=int(GetValue(listInfo,"code EPSG"))
    else: Projection=-1
    ### traitement différent pour le phasage
    if  (GetValue(listInfo,"CENTRE PIXEL") == ""):
        phasage="HG"
    else: phasage="CP"
        
    return [PasX,PasY,Projection,X_0,X_1,Y_0,Y_1,phasage,NbreCol,NbreLig,GModel,GRaster]       
      
############################################################################################################################         
def GetNbreDalleXDalleY(chemMNS_SousEch):

    infos=GetInfo(cmdxingng, chemMNS_SousEch)
    NbreCol=infos[8]
    NbreLig=infos[9]
        
    NombreDallesXY=CalculNombreDallesXY(NbreCol,NbreLig,iTailleparcelle,iTailleRecouvrement)
    NbreDalleX=int(NombreDallesXY[0])
    NbreDalleY=int(NombreDallesXY[1])

    return NbreDalleX, NbreDalleY

############################################################################################################################
def DecoupeParDalle(chemMNS_SousEch,chemMASQUE_SousEch,chemINIT_SousEch,NbreDalleX,NbreDalleY,iTailleparcelle,iTailleRecouvrement,RepTravail_tmp):
    
    count=0
    for x in range(NbreDalleX):
        for y in range(NbreDalleY):
            #créer le nom du répertoire
            RepDalleXY=os.path.join(RepTravail_tmp,"Dalle_%s_%s"%(x,y))
            #créer le répertoire, s'il n'existe pas déjà
            if not os.path.isdir(RepDalleXY): os.mkdir(RepDalleXY)
                
            #Détermination de col_min, col_max, lig_min, lig_max pour la dalle XY
            colminDalleXY=x*(iTailleparcelle-iTailleRecouvrement)
            colmaxDalleXY=x*(iTailleparcelle-iTailleRecouvrement)+iTailleparcelle
            ligminDalleXY=y*(iTailleparcelle-iTailleRecouvrement)
            ligmaxDalleXY=y*(iTailleparcelle-iTailleRecouvrement)+iTailleparcelle
                
            #fichier out mns
            ChemOUT_mns=os.path.join(RepDalleXY,"Out_MNS_%s_%s.tif"%(x,y))
                
            #fichier out masque
            ChemOUT_masque=os.path.join(RepDalleXY,"Out_MASQUE_%s_%s.tif"%(x,y))
                
            #fichier out masque
            ChemOUT_INIT=os.path.join(RepDalleXY,"Out_INIT_%s_%s.tif"%(x,y))
                
            #fichier out mnt
            ChemOUT_mnt=os.path.join(RepDalleXY,"Out_MNT_%s_%s.tif"%(x,y))
                
            ### crop MNS
            cmdCROP_mns = "%s -i %s -ci:%s:%s:%s:%s -o %s -n0 >> /dev/null 2>&1" % (cmdxingng, chemMNS_SousEch, ligminDalleXY, ligmaxDalleXY, colminDalleXY, colmaxDalleXY, ChemOUT_mns)
            #print(cmdCROP_mns)
            os.system(cmdCROP_mns)
                
            ### crop MASQUE        
            cmdCROP_masque = "%s -i %s -ci:%s:%s:%s:%s -o %s -n0 >> /dev/null 2>&1" % (cmdxingng, chemMASQUE_SousEch, ligminDalleXY, ligmaxDalleXY, colminDalleXY, colmaxDalleXY, ChemOUT_masque)
            #print(cmdCROP_masque)
            os.system(cmdCROP_masque)

            ### crop INIT
            cmdCROP_INIT = "%s -i %s -ci:%s:%s:%s:%s -o %s -n0 >> /dev/null 2>&1" % (cmdxingng, chemINIT_SousEch, ligminDalleXY, ligmaxDalleXY, colminDalleXY, colmaxDalleXY, ChemOUT_INIT)
            #print(cmdCROP_INIT)
            os.system(cmdCROP_INIT)

############################################################################################################################
def EcrireMakefile4Parallelisation(ChemMakefile,RepTravail_tmp,NbreDalleX,NbreDalleY,fsigma,flambda,norme):
            
    fic=open(ChemMakefile, "w")
    fic.write("all : ")

    count=0
    for x in range(NbreDalleX):
        for y in range(NbreDalleY):
            fic.write("tache%i " %count)
            count+=1
    fic.write("\n")
        
    count=0
    for x in range(NbreDalleX):
        for y in range(NbreDalleY):
            RepDalleXY=os.path.join(RepTravail_tmp,"Dalle_%s_%s"%(x,y))
                                
            #fichier out mns
            ChemOUT_mns=os.path.join(RepDalleXY,"Out_MNS_%s_%s.tif"%(x,y))
                
            #fichier out masque
            ChemOUT_masque=os.path.join(RepDalleXY,"Out_MASQUE_%s_%s.tif"%(x,y))
                
            #fichier out masque
            ChemOUT_INIT=os.path.join(RepDalleXY,"Out_INIT_%s_%s.tif"%(x,y))
                
            #fichier out mnt
            ChemOUT_mnt=os.path.join(RepDalleXY,"Out_MNT_%s_%s.tif"%(x,y))
                
            line="tache%i :\n" %count
            fic.write(line)
            line='\t%s -i %s %s %s -XG:%2.5f:%2.5f:%s:30000 -o %s -n: \n' %(cmdxingng_chem_complet,ChemOUT_mns,ChemOUT_masque,ChemOUT_INIT,fsigma,flambda,norme,ChemOUT_mnt)
            fic.write(line)
            count+=1
                
    fic.close()

    return

#################################################################################################### 
def RunGemoEnParallel(RepTravail_tmp, NbreDalleX, NbreDalleY, fsigma, flambda, norme, no_data_value, iNbreCPU):
    
    tasks = []

    for x in range(NbreDalleX):
        for y in range(NbreDalleY):
            RepDalleXY=os.path.join(RepTravail_tmp,"Dalle_%s_%s"%(x,y))
                                
            #fichier out mns
            ChemOUT_mns=os.path.join(RepDalleXY,"Out_MNS_%s_%s.tif"%(x,y))
                
            #fichier out masque
            ChemOUT_masque=os.path.join(RepDalleXY,"Out_MASQUE_%s_%s.tif"%(x,y))
                
            #fichier out masque
            ChemOUT_INIT=os.path.join(RepDalleXY,"Out_INIT_%s_%s.tif"%(x,y))
                
            #fichier out mnt
            ChemOUT_mnt=os.path.join(RepDalleXY,"Out_MNT_%s_%s.tif"%(x,y))
            
            # if os.path.exists(ChemOUT_mns):
            if contient_donnees(ChemOUT_mns, no_data_value):
                cmd_unitaire="%s -i %s %s %s -XG:%2.5f:%2.5f:%s:30000 -o %s -n0 >> /dev/null 2>&1" %(cmdxingng_chem_complet,ChemOUT_mns,ChemOUT_masque,ChemOUT_INIT,fsigma,flambda,norme,ChemOUT_mnt)
                #print(cmd_unitaire)
                tasks.append(cmd_unitaire)
            else:
                shutil.copyfile(ChemOUT_mns, ChemOUT_mnt)
                 
	# Initialize the pool
    with Pool(processes=iNbreCPU, initializer=init_worker) as pool:
        results = list(tqdm(pool.imap_unordered(os.system, tasks), total=len(tasks), desc="Lancement de GEMO unitaire en parallèle"))
		
        
    return

####################################################################################################
def contient_donnees_OLD(dalle, no_data_value=-9999):
    """
    Vérifie si une dalle contient des données valides.
    :param dalle: Tableau 2D représentant la dalle.
    :param no_data_value: Valeur correspondant à "no data".
    :return: True si la dalle contient des données valides, False sinon.
    """
    return not np.all(dalle == no_data_value)

####################################################################################################
def contient_donnees(chem_mns, no_data_value=-9999):
    # Ouvrir l'image raster
    with rasterio.open(chem_mns) as src:
        # Lire les données du raster dans un tableau numpy
        data = src.read(1)  # Lecture de la première bande (ou unique bande)
        return not np.all(data == no_data_value)

####################################################################################################
#traiter_dalle
def Decoupe_dalle(args):
    """
    Fonction qui traite une dalle sur trois images. Conçue pour être utilisée avec multiprocessing.
    :param args: Tuple contenant (mns_file, masque_file, init_file, x, y, largeur, hauteur, no_data_value, RepTravail_tmp).
    :return: Résultat du traitement (ou message).
    """
    mns_file, masque_file, init_file, col_dalle, lig_dalle, x_offset, y_offset, l_dalle, h_dalle, no_data_value, RepTravail_tmp = args

    # Lire les trois images avec rasterio
    with rasterio.open(mns_file) as mns_src, \
         rasterio.open(masque_file) as masque_src, \
         rasterio.open(init_file) as init_src:
        
        # Lire la dalle de MNS pour vérifier si elle contient des données valides
        mns_dalle = mns_src.read(1, window=Window(x_offset, y_offset, l_dalle, h_dalle))
   
        masque_dalle = masque_src.read(1, window=Window(x_offset, y_offset, l_dalle, h_dalle))
        init_dalle = init_src.read(1, window=Window(x_offset, y_offset, l_dalle, h_dalle))

        # Construire le chemin pour enregistrer les dalles en utilisant x et y
        RepDalleXY = os.path.join(RepTravail_tmp, f"Dalle_{col_dalle}_{lig_dalle}")
        os.makedirs(RepDalleXY, exist_ok=True)

        # Créer et sauvegarder les trois dalles (MNS, Masque, Initialisation)
        fichiers_dalles = {
            "mns": os.path.join(RepDalleXY, f"Out_MNS_{col_dalle}_{lig_dalle}.tif"),
            "masque": os.path.join(RepDalleXY, f"Out_MASQUE_{col_dalle}_{lig_dalle}.tif"),
            "init": os.path.join(RepDalleXY, f"Out_INIT_{col_dalle}_{lig_dalle}.tif")
        }
                
        # Sauvegarder les dalles dans des fichiers TIFF
        for name, dalle, src in zip(fichiers_dalles.keys(), [mns_dalle, masque_dalle, init_dalle], [mns_src, masque_src, init_src]):
            profil = src.profile
            profil.update({
                'height': h_dalle,
                'width': l_dalle,
                'transform': src.window_transform(Window(x_offset, y_offset, l_dalle, h_dalle))
            })
                
            # Sauvegarde de la dalle
            with rasterio.open(fichiers_dalles[name], 'w', **profil) as dst:
                dst.write(dalle, 1)

        # # Vérifier si la dalle contient des données valides dans l'image MNS
        # if contient_donnees(mns_dalle, no_data_value):
        #     # Lire les dalles pour les trois images
        #     masque_dalle = masque_src.read(1, window=Window(x_offset, y_offset, l_dalle, h_dalle))
        #     init_dalle = init_src.read(1, window=Window(x_offset, y_offset, l_dalle, h_dalle))

        #     # Construire le chemin pour enregistrer les dalles en utilisant x et y
        #     RepDalleXY = os.path.join(RepTravail_tmp, f"Dalle_{col_dalle}_{lig_dalle}")
        #     os.makedirs(RepDalleXY, exist_ok=True)

        #     # Créer et sauvegarder les trois dalles (MNS, Masque, Initialisation)
        #     fichiers_dalles = {
        #         "mns": os.path.join(RepDalleXY, f"Out_MNS_{col_dalle}_{lig_dalle}.tif"),
        #         "masque": os.path.join(RepDalleXY, f"Out_MASQUE_{col_dalle}_{lig_dalle}.tif"),
        #         "init": os.path.join(RepDalleXY, f"Out_INIT_{col_dalle}_{lig_dalle}.tif")
        #     }
                
        #     # Sauvegarder les dalles dans des fichiers TIFF
        #     for name, dalle, src in zip(fichiers_dalles.keys(), [mns_dalle, masque_dalle, init_dalle], [mns_src, masque_src, init_src]):
        #         profil = src.profile
        #         profil.update({
        #             'height': h_dalle,
        #             'width': l_dalle,
        #             'transform': src.window_transform(Window(x_offset, y_offset, l_dalle, h_dalle))
        #         })
                
        #         # Sauvegarde de la dalle
        #         with rasterio.open(fichiers_dalles[name], 'w', **profil) as dst:
        #             dst.write(dalle, 1)

        #     return f"Dalle {col_dalle}_{lig_dalle} en position ({col_dalle}, {lig_dalle}) traitée et enregistrée."
        # else:
        #     return f"Dalle {col_dalle}_{lig_dalle} en position ({col_dalle}, {lig_dalle}) ignorée (no data)."

#################################################################################################### 
def Decoupe_chantier(mns_file, masque_file, init_file, taille_dalle, iTailleRecouvrement, no_data_value, RepTravail_tmp, iNbreCPU):
    """
    Traite trois grandes images (MNS, Masque, Initialisation) en découpant en dalles avec chevauchement,
    et en utilisant multiprocessing pour accélérer le traitement, avec une barre de progression.
    :param mns_file: Chemin vers l'image MNS.
    :param masque_file: Chemin vers l'image de Masque.
    :param init_file: Chemin vers l'image d'Initialisation.
    :param taille_dalle: Tuple représentant la taille des dalles (hauteur, largeur).
    :param iTailleRecouvrement: Taille du recouvrement entre dalles en pixels.
    :param no_data_value: Valeur représentant "no data" pour MNS.
    :param RepTravail_tmp: Répertoire temporaire où enregistrer les dalles traitées.
    """

    with rasterio.open(mns_file) as mns_src:
        largeur = mns_src.width
        hauteur = mns_src.height

        h_dalle, l_dalle = taille_dalle  # Hauteur et largeur des dalles

        # Calculer le pas entre les dalles en fonction du recouvrement
        pas_x = l_dalle - iTailleRecouvrement  # Pas en X
        pas_y = h_dalle - iTailleRecouvrement  # Pas en Y

        # Calculer le nombre de dalles avec recouvrement
        NbreDalleX = (largeur - iTailleRecouvrement + pas_x - 1) // pas_x
        NbreDalleY = (hauteur - iTailleRecouvrement + pas_y - 1) // pas_y

        # Créer une liste des paramètres pour chaque dalle avec un compteur d'index
        params = []
        # index = 0  # Initialiser un compteur d'index global
        for x in range(NbreDalleX):
            for y in range(NbreDalleY):
                # Calculer la position (x, y) pour chaque dalle en fonction du pas
                x_offset = x * pas_x
                y_offset = y * pas_y

                # Calculer la largeur et hauteur de chaque bloc en respectant les bords
                l_bloc = min(l_dalle, largeur - x_offset)
                h_bloc = min(h_dalle, hauteur - y_offset)

                # Ajouter les paramètres pour traiter cette dalle
                params.append((mns_file, masque_file, init_file, x, y, x_offset, y_offset, l_bloc, h_bloc, no_data_value, RepTravail_tmp))

        # Utiliser multiprocessing pour traiter les dalles en parallèle avec une barre de progression
        with Pool(processes=iNbreCPU) as pool:
            # Utiliser tqdm pour la barre de progression
            results = list(tqdm(pool.imap_unordered(Decoupe_dalle, params), total=len(params), desc="Traitement des dalles"))

####################################################################################################
# Fonction pour exécuter gdal_translate via subprocess
def run_task_sans_SORTIEMESSAGE(cmd):
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

####################################################################################################
if __name__ == "__main__":
    
    try:

        start_time = time.time()
        start_time = time.time()
        # Création du parseur d'arguments avec une description et un épilogue pour l'exemple de commande
        parser = argparse.ArgumentParser(
            description='GEMAUT - Génération de Modèles Automatiques de Terrain',
            epilog="""EXEMPLE DE LIGNE DE COMMANDE:
            ./script_run_gemaut_refactoring.py --reso 2 [--sigma 0.5] [--regul 0.01] [--tile 300] --pad 120] [--norme hubertukey] --nodata_ext -32768 [--nodata_int -32767] --mns /chem/vers/MNS_in.tif [--init /chem/vers/MNS_in.tif] [--masque /chem/vers/MASQUE_GEMO.tif] --RepTra /chem/vers/RepTra --groundval 0 --out /chem/vers/MNT.tif --cpu 56 --clean
        
            IMPORTANT
            Le MNS doit avoir des valeurs de no_data différentes pour les bords de chantier [no_data_ext] et les trous à l'intérieur du chantier [no_data_int] là où la corrélation a échoué par exemple

        """
        )

        # Définition des arguments du programme
        parser.add_argument("--mns", type=str, required=True, help="input DSM")
        parser.add_argument("--masque", type=str, help="input ground/above-ground MASK")
        parser.add_argument("--init", type=str, help="initialisation [par défaut le MNS]")
        parser.add_argument("--out", type=str, required=True, help="output DTM")
        parser.add_argument("--RepTra", type=str, required=True, help="repertoire de Travail")
        parser.add_argument("--groundval", type=int, required=True, help="valeur de masque pour le SOL")
        parser.add_argument("--reso", type=float, required=True, default=4, help="resolution du MNT en sortie")
        parser.add_argument("--sigma", type=float, default=0.5, help="sigma / précision du Z MNS")
        parser.add_argument("--regul", type=float, default=0.01, help="regul / rigidité de la nappe")
        parser.add_argument("--tile", type=int, default=300, help="taille de la tuile")
        parser.add_argument("--pad", type=int, default=120, help="recouvrement entre tuiles")
        parser.add_argument("--cpu", type=int, required=True, help="nombre de CPUs à utiliser dans le traitement")
        parser.add_argument("--norme", type=str, default="hubertukey", help="choix entre les normes /tukey/huber/hubertukey/L1/L2")
        parser.add_argument("--nodata_ext", type=int, default=-32768, required=True, help="Valeur du no_data sur les bords de chantier")
        parser.add_argument("--nodata_int", type=int, default=-32767, help="Valeur du no_data pour les trous à l'intérieur du chantier")
        parser.add_argument("--clean", action='store_true', help="supprimer les fichiers temporaires à la fin du traitement")
        # Parsing des arguments
        args = parser.parse_args(sys.argv[1:])
        
        chemMNS_IN=args.mns 

        chemINIT=''
        if args.init is None:
            print('-- initialisation avec le MNS ')
            chemINIT=args.mns
        else:
            print('-- initialisation avec la donnée utilisateur >> ', args.init)
            chemINIT=args.init
        
        chemMNT_OUT=args.out
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

        ### 
        RepTravail_tmp=os.path.join(RepTravail,"tmp")
        if not os.path.isdir(RepTravail): os.mkdir(RepTravail)
        if not os.path.isdir(RepTravail_tmp): os.mkdir(RepTravail_tmp)

        ##
        chemMASQUE=''
        #
        if args.masque is None:
            # 
            print("Le masque n'a pas été fourni, il sera calculé à partir du MNS avec SAGA [via Docker] ")
            chemMASQUE=os.path.join(RepTravail,'MASQUE_compute.tif')
            taille_voisinage=5
            K=2
            percentile=5
            taille_dallage=20
            seuil_diff=15
            compute_ground_mask_parallel(chemMNS_IN,chemMASQUE,RepTravail_tmp,taille_voisinage,K,percentile,taille_dallage,seuil_diff,iNbreCPU)
        else:
            chemMASQUE=args.masque

        ###
        chemMNS_nodata_int_ext=os.path.join(RepTravail_tmp,'MNS_nodata_int_ext.tif')
        chemMNS=os.path.join(RepTravail_tmp,'MNS_sans_trou.tif')
        chemMNS_SousEch_tmp= os.path.join(RepTravail_tmp,'MNS_SousEch_tmp.tif')
        chemMNS_SousEch= os.path.join(RepTravail_tmp,'MNS_SousEch.tif')
        chemMASQUE_4gemo=os.path.join(RepTravail_tmp,'MASQUE_4gemo.tif')
        chemMASQUE_nodata=os.path.join(RepTravail_tmp,'MASQUE_nodata.tif')
        chemMASQUE_SousEch_tmp=os.path.join(RepTravail_tmp,'MASQUE_SousEch_tmp.tif')
        chemMASQUE_SousEch=os.path.join(RepTravail_tmp,'MASQUE_SousEch.tif')
        chemMNT_OUT_tmp=os.path.join(RepTravail_tmp,'OUT_MNT_tmp.tif')
        chemINIT_SousEch=os.path.join(RepTravail_tmp,'INIT.tif')
        ChemMakefile=os.path.join(RepTravail_tmp,'Makefile_parallel')   
        
        print("1/ Etiquetage et bouchage des no data")

        # On utilise foreval pour être dans la convention de GEMO: SOL = 0 / SURSOL =255
        cmd_masque4gemo="%s -i %s -e'I1.1==%d?0:255' -o %s -tuc -n0 > /dev/null 2>&1 " %(cmd_XinG,chemMASQUE,groundval,chemMASQUE_4gemo)
        os.system(cmd_masque4gemo)

        # Affectation d'une valeur spécifique pour gérer les bords de chantier = 11 (no_data_interne_mask)
        cmd_masque_nodata="%s -i %s %s -e'I2.1==%d?%d:I1.1' -o %s -tuc -n0 > /dev/null 2>&1 " %(cmd_XinG,chemMASQUE_4gemo,chemMNS_IN,no_data_ext,no_data_interne_mask,chemMASQUE_nodata)
        os.system(cmd_masque_nodata)

        ### label/étiquetage "trous"/"no data" internes et externes 
        ### >> maintenant on demande à l'utilisateur de le faire lui-même
        # OLD cmd_etiquetage_trous=" %s -i %s %s -e'((I2.1!=11)&&(I1.1=='%d'))?-32767:I1.1' -o %s -n: " %(cmd_XinG,chemMNS_IN,chemMASQUE,no_data,chemMNS_nodata_int_ext)
        # OLD os.system(cmd_etiquetage_trous)
        #
        # cmd_bouchage_trous="%s -i %s -FB:1:I:3:3:R-32767 -EM='%d',-32767 -o %s -n: " %(cmd_XinG,chemMNS_nodata_int_ext,no_data,chemMNS)
        cmd_bouchage_trous="%s -i %s -FB:1:I:3:3:R%d -EM=%d,%d -o %s -n0 > /dev/null 2>&1 " %(cmd_XinG,chemMNS_IN,no_data_int,no_data_ext,no_data_int,chemMNS)
        os.system(cmd_bouchage_trous)
        
        print("2/ Sous-échantillonnage pour travailler à la résolution de ", reso_travail, " mètres")
                
        ## SousEch de MNS et MASQUE 
        cmd_SousEch_MNS="gdalwarp -tr %2.10f %2.10f -srcnodata %d -dstnodata %d %s %s -overwrite" %(reso_travail,reso_travail,no_data_int,no_data_int,chemMNS,chemMNS_SousEch_tmp)
        run_task_sans_SORTIEMESSAGE(cmd_SousEch_MNS)
        
        ## SousEch de MASQUE
        cmd_SousEch_MASQUE="gdalwarp -tr %2.10f %2.10f -srcnodata %d -dstnodata %d %s %s -ot Byte -overwrite " %(reso_travail,reso_travail,no_data_interne_mask,no_data_interne_mask,chemMASQUE_nodata,chemMASQUE_SousEch_tmp)
        run_task_sans_SORTIEMESSAGE(cmd_SousEch_MASQUE)
        
        # SousEch de INIT
        cmd_SousEch_INIT="gdalwarp -tr %2.10f %2.10f %s %s -overwrite " %(reso_travail,reso_travail,chemINIT,chemINIT_SousEch)
        run_task_sans_SORTIEMESSAGE(cmd_SousEch_INIT)
        
        print("3/ GetNbreDalleXDalleY")         
        # pour retomber sur nos pattes au niveau des noms de variables...
        chemMASQUE_SousEch = chemMASQUE_SousEch_tmp
        NbreDalleX, NbreDalleY = GetNbreDalleXDalleY(chemMNS_SousEch_tmp)
                
        print("4/ Découpage des dalles pour chantier GEMAUT")    
        # print(chemMASQUE_SousEch)
        # print(chemINIT_SousEch)
        # print(iTailleparcelle)
        # print(iTailleRecouvrement)
        # print(no_data_ext)
        # print(RepTravail_tmp)
        # print(iNbreCPU)

        taille_dalle=(iTailleparcelle,iTailleparcelle)
        Decoupe_chantier(chemMNS_SousEch_tmp, chemMASQUE_SousEch, chemINIT_SousEch, taille_dalle, iTailleRecouvrement, no_data_ext, RepTravail_tmp, iNbreCPU)

        print("5/ Lancement en paralèle de GEMO") 
        RunGemoEnParallel(RepTravail_tmp, NbreDalleX, NbreDalleY, fsigma, flambda, norme, no_data_ext, iNbreCPU)

        print("6/ Raboutage avec xingng ")
        #### Assemblage final - avec xingng
        Raboutage(RepTravail_tmp,NbreDalleX,NbreDalleY,chemMNT_OUT_tmp)              
        ## Raboutage_OTB_BUG(RepTravail_tmp,NbreDalleX,NbreDalleY,chemMNT_OUT)

        #Gestion NoData dans Gemo OUT
        cmd_nodata=f"{cmdxingng} -i {chemMNT_OUT_tmp} {chemMNS_SousEch_tmp} -e'I2.1=={no_data_ext}?{no_data_ext}:I1.1' -o {chemMNT_OUT} -n0 >> /dev/null 2>&1"
        os.system(cmd_nodata)

        
        # rajouter une option DEBUG
        # suppression des fichiers temporaires 
        if args.clean:
            shutil.rmtree(RepTravail_tmp)
            print("7/ Nettoyage final")
                
        # Arrêter le chronomètre et calculer le temps écoulé
        end_time = time.time()
        elapsed_time = end_time - start_time  # Temps écoulé en secondes
        
        #Convertir le temps écoulé en heures, minutes, secondes
        formatted_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

        # Afficher le temps total de traitement
        print(f"Temps total de traitement: {formatted_time}")        
		
        print("END")

#==================================================================================================
# Gestion des exceptions
#==================================================================================================
    except (RuntimeError, TypeError, NameError):
        print ("ERREUR: ", NameError)

