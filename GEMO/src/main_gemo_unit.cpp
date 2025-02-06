#include <iostream>
#include <opencv2/opencv.hpp>
# include "GEA.h"
#include <opencv2/opencv.hpp>
#include <iostream>
//#include <gdal/gdal_priv.h>
#include <gdal_priv.h>

//#include <gdal/cpl_conv.h>  // for CPLMalloc()

/*
int main()
{
    // Chemin vers votre fichier MNS
    std::string chemin = "DATA_TEST/Dalle_0_0/Out_MNS_0_0.tif";

    // Lire l'image en tant que float32
    cv::Mat image = cv::imread(chemin, cv::IMREAD_GRAYSCALE);

    // Vérifier si l'image est bien chargée
    if (image.empty())
    {
        std::cerr << "Erreur : Impossible de charger l'image." << std::endl;
        return -1;
    }

    // Vérifier le type de l'image
    if (image.type() != CV_32FC1)
    {
        std::cerr << "L'image n'est pas au format float32." << std::endl;
        return -1;
    }

    // Afficher quelques informations sur l'image
    std::cout << "Dimensions de l'image : " << image.rows << "x" << image.cols << std::endl;
    std::cout << "Type de l'image : " << image.type() << std::endl;

    // Accéder aux données pour vérifier des valeurs (par exemple au centre de l'image)
    float altitude = image.at<float>(image.rows / 2, image.cols / 2);
    std::cout << "Altitude au centre de l'image : " << altitude << std::endl;

    return 0;
}
*/


/*
void saveWithGeoReference(const std::string& inputFilename, cv::Mat& image, const std::string& outputFilename) {
    // Ouvrir l'image d'entrée
    GDALAllRegister(); // S'assurer que tous les drivers GDAL sont enregistrés
    GDALDataset* inputDataset = (GDALDataset*)GDALOpen(inputFilename.c_str(), GA_ReadOnly);
    if (inputDataset == nullptr) {
        std::cerr << "Erreur lors de l'ouverture du fichier d'entrée : " << inputFilename << std::endl;
        return;
    }
*/
    
void saveWithGeoReference(const std::string& inputFilename, cv::Mat& image, const std::string& outputFilename) {
    // Ouvrir l'image d'entrée
    GDALAllRegister(); // S'assurer que tous les drivers GDAL sont enregistrés
    GDALDataset* inputDataset = (GDALDataset*)GDALOpen(inputFilename.c_str(), GA_ReadOnly);
    if (inputDataset == nullptr) {
        std::cerr << "*** Erreur lors de l'ouverture du fichier d'entrée : " << inputFilename << std::endl;
        return;
    }

    // Récupérer les informations géoréférencées de l'image d'entrée
    double geoTransform[6];
    if (inputDataset->GetGeoTransform(geoTransform) != CE_None) {
        std::cerr << "Erreur lors de l'obtention des informations géoréférencées de l'image d'entrée." << std::endl;
        GDALClose(inputDataset);
        return;
    }

    const char* projection = inputDataset->GetProjectionRef();
    const char* areaOrPoint = inputDataset->GetMetadataItem("AREA_OR_POINT");

    // Créer l'image de sortie
    GDALDriver* driver = GetGDALDriverManager()->GetDriverByName("GTiff");
    if (driver == nullptr) {
        std::cerr << "Erreur lors de la récupération du driver GTiff." << std::endl;
        GDALClose(inputDataset);
        return;
    }

    GDALDataset* outputDataset = driver->Create(outputFilename.c_str(), image.cols, image.rows, 1, GDT_Float64, nullptr);
    if (outputDataset == nullptr) {
        std::cerr << "Erreur lors de la création du fichier de sortie : " << outputFilename << std::endl;
        GDALClose(inputDataset);
        return;
    }

    // Appliquer les informations géoréférencées à l'image de sortie
    outputDataset->SetGeoTransform(geoTransform);
    outputDataset->SetProjection(projection);

    // Appliquer la métadonnée "AREA_OR_POINT" de l'image d'entrée à l'image de sortie
    outputDataset->SetMetadataItem("AREA_OR_POINT", areaOrPoint);

    // Écrire les données de l'image OpenCV dans l'image de sortie GDAL
    GDALRasterBand* band = outputDataset->GetRasterBand(1);
    //band->RasterIO(GF_Write, 0, 0, image.cols, image.rows, image.ptr<double>(), image.cols, image.rows, GDT_Float64, 0, 0);
	CPLErr err = band->RasterIO(GF_Write, 0, 0, image.cols, image.rows, image.ptr<double>(), image.cols, image.rows, GDT_Float64, 0, 0);
	if (err != CE_None) std::cerr << "-- Erreur lors de l'écriture des données dans le fichier TIFF : " << CPLGetLastErrorMsg() << std::endl;

    // Fermer les datasets
    GDALClose(outputDataset);
    GDALClose(inputDataset);

    //std::cout << "L'image a été enregistrée avec les informations géoréférencées." << std::endl;
}


/*
    // Écrire les données de l'image OpenCV dans l'image de sortie GDAL
    GDALRasterBand* band = outputDataset->GetRasterBand(1);
	CPLErr err = band->RasterIO(GF_Write, 0, 0, image.cols, image.rows, image.ptr<double>(), image.cols, image.rows, GDT_Float64, 0, 0);
	if (err != CE_None) std::cerr << "-- Erreur lors de l'écriture des données dans le fichier TIFF : " << CPLGetLastErrorMsg() << std::endl;
*/



int main(int argc, char *argv[]) 
{
    if ( (argc < 8) || (argc > 9) )
        {
            std::cout << " -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*- " << std::endl;        
            std::cout << " -*-*-*-*-*-*     USAGE     *-*-*-*-*-*-*- " << std::endl;        
            std::cout << " -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*- " << std::endl;
            
        	std::cout << " ./main_gea_unit                  " <<std::endl ;
        	std::cout << "          MNE_en_entrée " <<std::endl ;
        	std::cout << "          Masque_en_entrée " <<std::endl ;        	
	        std::cout << "          Solut_Init " <<std::endl ;   
	        std::cout << "          MNT_out " <<std::endl ;   	                 
	        std::cout << "          sigma               [0.5] " <<std::endl ;  
	        std::cout << "          lambda              [0.02] " <<std::endl ;  
	        std::cout << "          no data ext         [no data ext]" <<std::endl ; 
	        std::cout << "          norme               [hubertukey]" <<std::endl ;  	        
            return 1 ;
        }

    std::string Nom_MNE = argv[1];
    std::string Nom_Masque = argv[2];
    std::string Nom_Solut_Init = argv[3];
    std::string Nom_MNT = argv[4];
    float sigma = std::stof(argv[5]);
    float lambda = std::stof(argv[6]);
    float no_data_ext = std::stof(argv[7]);
    std::string Nom_norme = (argc == 9) ? argv[8] : "hubertukey";

    // Lire les images
    cv::Mat TTIma_MNE = cv::imread(Nom_MNE, cv::IMREAD_UNCHANGED);
    cv::Mat TTIma_Masque = cv::imread(Nom_Masque, cv::IMREAD_UNCHANGED);
    cv::Mat TTIma_Solut_Init = cv::imread(Nom_Solut_Init, cv::IMREAD_UNCHANGED);
	cv::Mat TTIma_MNT;  // Ce sera notre sortie

    if (TTIma_MNE.empty() || TTIma_Masque.empty() || TTIma_Solut_Init.empty()) {
        std::cerr << "Erreur de lecture des images." << std::endl;
        return 1;
    }

    //std::cout << "Nom_norme: " << Nom_norme << std::endl;
    //std::cout << "sigma: " << sigma << std::endl;
    //std::cout << "lambda: " << lambda << std::endl;

    // Appeler GEA pour traiter les données    
    GEA(TTIma_MNE, TTIma_Masque, TTIma_Solut_Init, TTIma_MNT, Nom_norme, sigma, lambda, no_data_ext);
    
    // Sauvegarder le résultat
    //cv::imwrite(Nom_MNT, TTIma_MNT);
	saveWithGeoReference(Nom_MNE, TTIma_MNT, Nom_MNT);
	
    return 0;
}
