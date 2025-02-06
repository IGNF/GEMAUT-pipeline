#include "Parametres.h"
#include <opencv2/opencv.hpp> // Ensure you're including OpenCV for cv::Mat
#include <iostream> // For std::cerr
#include <cstdlib>  // For exit


// Constructeur de la classe Parametres
Parametres::Parametres(const cv::Mat& TTIma_MNE, const cv::Mat& TTIma_Masque, TPoint2D<double> SortieMinMax, const std::string& NOM_norme, float sigma, float lambda)
{

	
	int type = TTIma_Masque.type();

	/*
	// Tester les types liés aux entiers
	if (type == CV_8U) {
		std::cout << "Le type est CV_8U (unsigned 8-bit)" << std::endl;
	} else if (type == CV_8S) {
		std::cout << "Le type est CV_8S (signed 8-bit)" << std::endl;
	} else if (type == CV_16U) {
		std::cout << "Le type est CV_16U (unsigned 16-bit)" << std::endl;
	} else if (type == CV_16S) {
		std::cout << "Le type est CV_16S (signed 16-bit)" << std::endl;
	} else if (type == CV_32S) {
		std::cout << "Le type est CV_32S (signed 32-bit)" << std::endl;
	} else if (type == CV_32F) {
		std::cout << "Le type est CV_32F (float 32-bit)" << std::endl;
	} else if (type == CV_64F) {
		std::cout << "Le type est CV_64F (double 64-bit)" << std::endl;
	} else if (type == CV_8UC1) {
		std::cout << "Le type est CV_8UC1 (unsigned 8-bit, 1 channel)" << std::endl;
	} else if (type == CV_16UC1) {
		std::cout << "Le type est CV_16UC1 (unsigned 16-bit, 1 channel)" << std::endl;
	} else if (type == CV_32FC1) {
		std::cout << "Le type est CV_32FC1 (float 32-bit, 1 channel)" << std::endl;
	} else if (type == CV_64FC1) {
		std::cout << "Le type est CV_64FC1 (double 64-bit, 1 channel)" << std::endl;
	} else {
		std::cout << "Type inconnu" << std::endl;
	}
	*/

    m_taille.x = TTIma_Masque.cols;  // Use cols for number of columns
    m_taille.y = TTIma_Masque.rows;  // Use rows for number of rows
    m_SortieMin = static_cast<int>(SortieMinMax.x);  // Use .x and .y for TPoint2D
    m_SortieMax = static_cast<int>(SortieMinMax.y);
    m_sigma = sigma;
    m_lambda = lambda;

	//std::cout << "m_taille.x >> " << m_taille.x << std::endl ;
	//std::cout << "m_taille.y >> " << m_taille.y << std::endl ;
	//std::cout << "m_SortieMin >> " << m_SortieMin << std::endl ;
	//std::cout << "m_SortieMax >> " << m_SortieMax << std::endl ;
	//std::cout << "m_sigma >> " << m_sigma << std::endl ;
	//std::cout << "m_lambda >> " << m_lambda << std::endl ;
	
    // Définition de la norme (now using std::string)
    if (NOM_norme == "huber")
    {
        m_norme = new NormeHuber();
    }
    else if (NOM_norme == "tukey")
    {
        m_norme = new NormeTukey();
    }
    else if (NOM_norme == "hubertukey")
    {
        m_norme = new NormeHuberTukey();
    }
    else if (NOM_norme == "L2")
    {
        m_norme = new NormeL2();
    }
    else
    {
        std::cerr << "Erreur Class Parametres, argument constructeur : NOM_norme" << std::endl;
        exit(0);
    }
    
	//std::cout << " ****** Type of TTIma_MNE: " << TTIma_MNE.type() << std::endl;
	
    // Processing image data into vectors...
    for (int y = 0; y < TTIma_Masque.rows; ++y)
    {
        for (int x = 0; x < TTIma_Masque.cols; ++x)
        {
            m_pil_Masque.push_back(TTIma_Masque.at<unsigned char>(y, x));  // Use .at for matrix access
            m_pil_MNE.push_back(TTIma_MNE.at<float>(y, x));                // Use .at for matrix access
        }
    }
	//std::cout << " ***** fin remplissage " << std::endl ;
    // Initialization of TTIma_Pix_TypeDerive
    cv::Mat TTIma_Pix_TypeDerive = cv::Mat::zeros(TTIma_Masque.size(), CV_32S);  // CV_32S for int type

    int iTypeDeriveG;
    int iTypeDeriveD;

	int count = 0;
    // Identification_Dérivee_Pixel_X
    for (int y = 0; y < TTIma_Masque.rows; ++y)
    {
        iTypeDeriveG = 0;
        iTypeDeriveD = 0;

        for (int x = 0; x < TTIma_Masque.cols; ++x)
        {
            if (TTIma_Masque.at<unsigned char>(y, x) != 11)
            {
                TTIma_Pix_TypeDerive.at<int>(y, x) += iTypeDeriveG;
                if (iTypeDeriveG < 2) iTypeDeriveG++;
            }
            else
            {
					count += 1;
                TTIma_Pix_TypeDerive.at<int>(y, x) = -1;
                iTypeDeriveG = 0;
            }

            if (TTIma_Masque.at<unsigned char>(y, TTIma_Masque.cols - 1 - x) != 11)
            {
                TTIma_Pix_TypeDerive.at<int>(y, TTIma_Masque.cols - 1 - x) += iTypeDeriveD;
                if (iTypeDeriveD < 6) iTypeDeriveD += 3;
            }
            else
            {
				count += 1;
                TTIma_Pix_TypeDerive.at<int>(y, TTIma_Masque.cols - 1 - x) = -1;
                iTypeDeriveD = 0;
            }
        }
    }
	//std::cout << "count >> " << count << std::endl ;
    // Identification_Dérivee_Pixel_Y
    for (int x = 0; x < TTIma_Masque.cols; ++x)
    {
        iTypeDeriveG = 0;
        iTypeDeriveD = 0;

        for (int y = 0; y < TTIma_Masque.rows; ++y)
        {
            if (TTIma_Masque.at<unsigned char>(y, x) != 11)
            {
                TTIma_Pix_TypeDerive.at<int>(y, x) += iTypeDeriveG;
                if (iTypeDeriveG < 20) iTypeDeriveG += 10;
            }
            else
            {
                TTIma_Pix_TypeDerive.at<int>(y, x) = -1;
                iTypeDeriveG = 0;
            }

            if (TTIma_Masque.at<unsigned char>(TTIma_Masque.rows - 1 - y, x) != 11)
            {
                TTIma_Pix_TypeDerive.at<int>(TTIma_Masque.rows - 1 - y, x) += iTypeDeriveD;
                if (iTypeDeriveD < 60) iTypeDeriveD += 30;
            }
            else
            {
                TTIma_Pix_TypeDerive.at<int>(TTIma_Masque.rows - 1 - y, x) = -1;
                iTypeDeriveD = 0;
            }
        }
    }

    // Updating m_pil_Pix_TypeDerive_X and m_pil_Pix_TypeDerive_Y
    for (int y = 0; y < TTIma_Pix_TypeDerive.rows; ++y)
    {
        for (int x = 0; x < TTIma_Pix_TypeDerive.cols; ++x)
        {
            int iTypeDeriveY = TTIma_Pix_TypeDerive.at<int>(y, x) / 10;
            int iTypeDeriveX = TTIma_Pix_TypeDerive.at<int>(y, x) - 10 * iTypeDeriveY;

            // Adjust values as per original logic
            if (iTypeDeriveY == 6) iTypeDeriveY = 4;
            else if (iTypeDeriveY == 4) iTypeDeriveY = 6;

            if (iTypeDeriveX == 6) iTypeDeriveX = 4;
            else if (iTypeDeriveX == 4) iTypeDeriveX = 6;

            m_pil_Pix_TypeDerive_X.push_back(iTypeDeriveX);
            m_pil_Pix_TypeDerive_Y.push_back(iTypeDeriveY);
        }
    }
}

// Destructeur de la classe Parametres
Parametres::~Parametres()
{
    delete m_norme;
}

