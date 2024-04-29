#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys, os, math, time, glob, shutil
import argparse

#==================================================================================================
# Usage
#==================================================================================================
# def Usage():
    # print """
# USAGE :
# Version du 08/12/2020

# Génération de MNT avec GEMAUT(Génération et Modélisation AUtomatique du Terrain)

### ./script_run_gemaut.py  
            ### /chemin/vers/MNS.tif                 ### /chemin/vers/MNS.tif 
            ### /chemin/vers/MASQUE.tif             ### /chemin/vers/MASQUE.tif
            ### /chemin/vers/repertoire/OUT_GEMAUT     ### /chemin/vers/repertoire/OUT
            ### -downsampling 4 [en mètres]            ### Résolution de travail
            ### -sigma 0.5                             ### coefficient_sigma
            ### -regul 0.01                         ### coefficient_lambda
            ### -tile 300                             ### taille_dalle_decoupage_chantier
            ### -pad 120                             ### recouv_dalle_chantier
            ### -cpu 20                              ### nombre_processeurs_a_utiliser
            ### -norme hubertukey                    ### norme à utiliser
#
# """     

cmd_XinG='_XinG'
cmdxingng='xingng'
#cmdxingng_chem_complet='/Volumes/ALI_Serveur/OUTILS_IGNE/OUTILS_EIDS/bin_linux/xingng'
cmdxingng_chem_complet='/Volumes/ALI_Serveur/DEPLOIEMENT/bin_linux/xingng' 
   
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
    cmdinfo="%s -i %s  -n:stdout" % (cmdxingng,chemMNS)
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
      
#==================================================================================================
# Main
#==================================================================================================

### reste à faire -- norme -- lambda + sigma !! à rendre paramétrable !

if __name__ == "__main__":
    
    try:
        
# Génération de MNT avec GEMAUT(Génération et Modélisation AUtomatique du Terrain)

### ./script_run_gemaut.py  
            ### /chemin/vers/MNS.tif                 ### /chemin/vers/MNS.tif 
            ### /chemin/vers/MASQUE.tif             ### /chemin/vers/MASQUE.tif
            ### /chemin/vers/repertoire/OUT_GEMAUT     ### /chemin/vers/repertoire/OUT
            ### -downsampling 4 [en mètres]            ### Résolution de travail
            ### -sigma 0.5                             ### coefficient_sigma
            ### -regul 0.01                         ### coefficient_lambda
            ### -tile 300                             ### taille_dalle_decoupage_chantier
            ### -pad 120                             ### recouv_dalle_chantier
            ### -cpu 20                              ### nombre_processeurs_a_utiliser
            ### -norme hubertukey                    ### norme à utiliser
            
        parser = argparse.ArgumentParser(description='GEMAUT - Génération de Modèles Automatiques de Terrain')
        parser.add_argument("in_dsm", type=str, help="input DSM")
        parser.add_argument("in_mask", type=str, help="input ground/above-ground MASK")
        parser.add_argument("out", type=str, help="output directory")
        #parser.add_argument("-mask", "--mask", nargs="+", type=str, default=None, help="Mask for forest")
        parser.add_argument("-downsampling", type=float, default=4, help="[en mètres] downsampling rate / Coeeficient de sous-échantillonnage")
        parser.add_argument("-sigma", type=float, default=0.5, help="sigma / précision de l'altimétrie dans le MNS")
        parser.add_argument("-regul", type=float, default=0.01, help="regul / rigidité de la surface à reconstruire")
        parser.add_argument("-tile", type=int, default=300, help="Tile / Taille de la tuile")
        parser.add_argument("-pad", type=int, default=120, help="Pad / Recouvrement entre tuiles")
        parser.add_argument("-cpu", type=int, default=8, help="number of CPUs to use / Nbre de CPUs à utiliser dans le traitement")
        parser.add_argument("-norme", type=str, default="hubertukey", help="choix entre hubertukey/tukey/huber/L2")
        #parser.add_argument("-tile_BigTif", type=int, default=20000, help="Tile Big Tiff / Taille de la tuile pour Big Tiff")
        #parser.add_argument("-pad_BigTif", type=int, default=1000, help="Pad Big Tiff / Recouvrement entre tuiles pour Big Tiff")
        
        args = parser.parse_args(sys.argv[1:])
        
        chemMNS_IN=args.in_dsm 
        chemMASQUE=args.in_mask 
        RepTravail=args.out
        reso_travail=args.downsampling
        fsigma=args.sigma
        flambda=args.regul
        iTailleparcelle=args.tile
        iTailleRecouvrement=args.pad
        iNbreCPU=args.cpu
        norme=args.norme
        #Taille_dalle_BTiff=args.tile_BigTif 
        #Recouv_entre_dalles_BTiff=args.pad_BigTif
        ### modification de PATH pour avoir accès aux exécutables locaux main_GEMAUT_unit
        ##os.environ['PATH'] = "%s:%s" %(os.environ['PATH'],os.path.dirname(chem_exe_GEMAUT_parallel))

        ### 
        RepTravail_tmp=os.path.join(RepTravail,"tmp")
        if not os.path.isdir(RepTravail): os.mkdir(RepTravail)
        if not os.path.isdir(RepTravail_tmp): os.mkdir(RepTravail_tmp)
        
        ###
        chemMNS_nodata_int_ext=os.path.join(RepTravail_tmp,'MNS_nodata_int_ext.tif')
        chemMNS=os.path.join(RepTravail,'MNS_sans_trou.tif')
        chemMNS_SousEch_tmp= os.path.join(RepTravail_tmp,'MNS_SousEch_tmp.tif')
        chemMNS_SousEch= os.path.join(RepTravail_tmp,'MNS_SousEch.tif')
        chemMASQUE_SousEch_tmp=os.path.join(RepTravail_tmp,'MASQUE_SousEch_tmp.tif')
        chemMASQUE_SousEch=os.path.join(RepTravail_tmp,'MASQUE_SousEch.tif')
        ChemMakefile=os.path.join(RepTravail_tmp,'Makefile_parallel')
        fic=open(ChemMakefile, "w")
        fic.write("all : ")
        
        print("1/ Etiquetage et bouchage des no data")
        
        ### label/étiquetage "trous"/"no data" internes et externes 
        cmd_etiquetage_trous=" %s -i %s %s -e'((I2.1!=11)&&(I1.1==-32768))?-32767:I1.1' -o %s -n: " %(cmd_XinG,chemMNS_IN,chemMASQUE,chemMNS_nodata_int_ext)
        print(cmd_etiquetage_trous)    
        os.system(cmd_etiquetage_trous)
        cmd_bouchage_trous="%s -i %s -FB:1:I:3:3:R-32767 -EM=-32768,-32767 -o %s -n: " %(cmd_XinG,chemMNS_nodata_int_ext,chemMNS)
        print(cmd_bouchage_trous)
        os.system(cmd_bouchage_trous)
        
        print("2/ Sous-échantillonnage pour travailler à la résolution de ", reso_travail, " mètres")
                
        ## SousEch de MNS et MASQUE
        cmd_SousEch_MNS="gdalwarp -tr %2.10f %2.10f %s %s " %(reso_travail,reso_travail,chemMNS,chemMNS_SousEch_tmp)
        print("cmd_SousEch_MNS      >>> ",chemMNS_SousEch_tmp)
        #cmd_SousEch_MNS_bis="gdalwarp -tr %2.10f %2.10f -srcnodata -32768 -dstnodata -32768 %s %s " %(reso_travail,reso_travail,chemMNS,chemMNS_SousEch)
        #print("cmd_SousEch_MNS_bis  >>> ",cmd_SousEch_MNS_bis)
        os.system(cmd_SousEch_MNS)
        
        ## SousEch de MASQUE
        cmd_SousEch_MASQUE="gdalwarp -tr %2.10f %2.10f %s %s " %(reso_travail,reso_travail,chemMASQUE,chemMASQUE_SousEch_tmp)
        print("cmd_SousEch_MASQUE >>> ",cmd_SousEch_MASQUE)
        #cmd_SousEch_MASQUE_bis="gdalwarp -tr %2.10f %2.10f  -srcnodata -32768 -dstnodata -32768 %s %s " %(reso_travail,reso_travail,chemMASQUE,chemMASQUE_SousEch)
        #print("cmd_SousEch_MASQUE_bis >>> ",cmd_SousEch_MASQUE_bis)        
        os.system(cmd_SousEch_MASQUE)
        
        cmd_clean="%s -i %s %s -e'((I1.1==11)||(I2.1<-10000))?11:I1.1' -o %s -tuc " %(cmdxingng,chemMASQUE_SousEch_tmp,chemMNS_SousEch_tmp,chemMASQUE_SousEch)
        print(cmd_clean)
        os.system(cmd_clean)
        
        cmd_clean2="%s -i %s %s -e'((I1.1<-10000)||(I2.1==11))?-32768:I1.1' -o %s  " %(cmdxingng,chemMNS_SousEch_tmp,chemMASQUE_SousEch_tmp,chemMNS_SousEch)
        print(cmd_clean2)
        os.system(cmd_clean2)
        
        print("3/ Découpage des dalles pour chantier GEMAUT")
        
        infos=GetInfo(cmdxingng, chemMNS_SousEch)
        NbreCol=infos[8]
        NbreLig=infos[9]
        
        NombreDallesXY=CalculNombreDallesXY(NbreCol,NbreLig,iTailleparcelle,iTailleRecouvrement)
        NbreDalleX=NombreDallesXY[0]
        NbreDalleY=NombreDallesXY[1]
        
        count=0
        for x in range(NbreDalleX):
            for y in range(NbreDalleY):
                fic.write("tache%i " %count)
                count+=1
        fic.write("\n")
        
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
                
                #fichier out mnt
                ChemOUT_mnt=os.path.join(RepDalleXY,"Out_MNT_%s_%s.tif"%(x,y))
                
                ### crop MNS
                cmdCROP_mns = "%s -i %s -ci:%s:%s:%s:%s -o %s -n:" % (cmdxingng, chemMNS_SousEch, ligminDalleXY, ligmaxDalleXY, colminDalleXY, colmaxDalleXY, ChemOUT_mns)
                os.system(cmdCROP_mns)
                
                ### crop MASQUE        
                cmdCROP_masque = "%s -i %s -ci:%s:%s:%s:%s -o %s -n:" % (cmdxingng, chemMASQUE_SousEch, ligminDalleXY, ligmaxDalleXY, colminDalleXY, colmaxDalleXY, ChemOUT_masque)
                os.system(cmdCROP_masque)
                
                line="tache%i :\n" %count
                fic.write(line)
                line='\t%s -i %s %s %s -XG:%2.5f:%2.5f:%s:30000 -o %s -n: \n' %(cmdxingng_chem_complet,ChemOUT_mns,ChemOUT_masque,ChemOUT_mns,fsigma,flambda,norme,ChemOUT_mnt)
                print(">>> ",line)
                fic.write(line)
                count+=1
                
        fic.close()
        
        print("4/ Lancement parallèle brique unitaire") 
        
        print(ChemMakefile)
        cmd_parallel="make -f %s -j%i" %(ChemMakefile,iNbreCPU)
        print("cmd_parallel >>> %s " %cmd_parallel)
        os.system(cmd_parallel)
        
        print("5/ Raboutage - blending ")
        #### Assemblage final - avec xingng
        
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
                #
                #### chem_MNS_dalle=os.path.join(RepDalleXY,'MNS.tif')
                #### chem_MASQUE_dalle=os.path.join(RepDalleXY,'MASQUE.tif')
                #### chem_MNT_GEMAUT_OUT=os.path.join(RepDalleXY_OUT,'Out_MNT.tif')
                #### chem_MNT_GEMAUT_OUT_float32=os.path.join(RepDalleXY_OUT,'Out_MNT_float32.tif')
                #### chem_MNT_GEMAUT_OUT_float32_georef=os.path.join(RepDalleXY_OUT,'Out_MNT_float32_georef.tif')
                #
                
                ## IMAGE GAUCHE / IMAGE DROITE <> DALLE_0_0 / DALLE_1_0 !
                cmd_1="%s -i %s %s -X- -o %s -n:" %(cmdxingng,chem_MNT_GEMAUT_OUT_dalle_xy,chem_MNT_GEMAUT_OUT_dalle_xy_droite, os.path.join(RepTravail_tmp,'diff_tmp.tif'))
                print(cmd_1)
                os.system(cmd_1)

                cmd_2="%s -i %s -e'C/NC' -o  %s -tf -n:" %(cmdxingng,os.path.join(RepTravail_tmp,'diff_tmp.tif'),os.path.join(RepTravail_tmp,'poids_HG_HD_pour_HD.tif'))
                print(cmd_2)
                os.system(cmd_2)
                
                cmd_3="%s -i %s -e'1-I1' -o  %s -n:" %(cmdxingng,os.path.join(RepTravail_tmp,'poids_HG_HD_pour_HD.tif'),os.path.join(RepTravail_tmp,'poids_HG_HD_pour_HG.tif'))
                print(cmd_3)
                os.system(cmd_3)
                
                liste_info_tmp=GetInfo(cmdxingng, os.path.join(RepTravail_tmp,'poids_HG_HD_pour_HD.tif'))

                cmd_final="%s -i %s %s %s %s -e'I1*I2+I3*I4' -o %s -cg:%s:%s:%s:%s -n:" %(cmdxingng,chem_MNT_GEMAUT_OUT_dalle_xy,
                                                                                    os.path.join(RepTravail_tmp,'poids_HG_HD_pour_HG.tif'),
                                                                                    chem_MNT_GEMAUT_OUT_dalle_xy_droite, 
                                                                                    os.path.join(RepTravail_tmp,'poids_HG_HD_pour_HD.tif'),
                                                                                    os.path.join(RepTravail_tmp,'reconstruction_dalle_%s_%s_%s.tif' %(x,x+1,y)),
                                                                                    liste_info_tmp[3],
                                                                                    liste_info_tmp[4],
                                                                                    liste_info_tmp[5],
                                                                                    liste_info_tmp[6])
                                                                                                                                                                    
                print(cmd_final)
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
            
            print(cmd_assemblage_final_par_ligne)
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
            print(cmd_1)
            os.system(cmd_1)
            
            cmd_2="%s -i %s -e'L/NL' -o %s -tf -n:" %(cmdxingng,os.path.join(RepTravail_tmp,'diff_tmp.tif'),os.path.join(RepTravail_tmp,'poids_HG_BG_pour_BG.tif'))
            print(cmd_2)
            os.system(cmd_2)
            
            cmd_3="%s -i %s -e'1-I1' -o %s -n:" %(cmdxingng,os.path.join(RepTravail_tmp,'poids_HG_BG_pour_BG.tif'),os.path.join(RepTravail_tmp,'poids_HG_BG_pour_HG.tif'))
            print(cmd_3)
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
            print(cmd_final)
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
        
        chemMNT_OUT=os.path.join(RepTravail,"OUT_MNT_GEMAUT_final.tif")
        str_tmp=" -a -o %s -n:" %chemMNT_OUT
        cmd_assemblage_final+=str_tmp
            
        print(cmd_assemblage_final)
        os.system(cmd_assemblage_final)            
        
#         print "5/ Raboutage - blending final" 
#         
#         #### Assemblage final - avec OTB buggué
#         cmd_blending="/home/OTB/OTB-7.1.0-Linux64/bin/otbcli_Mosaic -il "
#                 
#         ## lancement de LSL sur chaque dalle    
#         for x in range(NbreDalleX):
#             for y in range(NbreDalleY):
#                 ## Nom de la dalle courante
#                 RepDalleXY=os.path.join(RepTravail_tmp,"Dalle_%s_%s"%(x,y))
#                 chem_out=os.path.join(RepDalleXY,"Out_MNT_%s_%s.tif"%(x,y))
#                 cmd_blending_tmp="%s %s " %(cmd_blending,chem_out)
#                 cmd_blending=cmd_blending_tmp
#                 
#         chemMNT_OUT=os.path.join(RepTravail,"OUT_MNT_GEMAUT_final.tif")
#                     
#         cmd_blending_final="%s -comp.feather large -out %s -progress 0 " %(cmd_blending,chemMNT_OUT)
#         print(cmd_blending_final)
#         os.system(cmd_blending_final)
#                 
        
        print("6/ Nettoyage final")
        #shutil.rmtree(RepTravail_tmp)
        
        print("7/ Fin")
        
#==================================================================================================
# Gestion des exceptions
#==================================================================================================
    except (RuntimeError, TypeError, NameError):
        print ("ERREUR: ", NameError)
        #Usage()


