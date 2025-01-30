#include <iostream>
#include <opencv2/opencv.hpp>
#include <gsl/gsl_multimin.h>
#include "GEA.h"

/*

struct Parametres {
    cv::Mat mne_min_max;
    cv::Mat TTIma_Masque;
    cv::Point2d SortieMinMax;
    std::string NOM_norme;
    float sigma;
    float lambda;
    Parametres(const cv::Mat& mne_min_max, const cv::Mat& TTIma_Masque, const cv::Point2d& SortieMinMax,
               const std::string& NOM_norme, float sigma, float lambda)
        : mne_min_max(mne_min_max), TTIma_Masque(TTIma_Masque), SortieMinMax(SortieMinMax),
          NOM_norme(NOM_norme), sigma(sigma), lambda(lambda) {}
};

*/

/*
// Définir ici les fonctions de calcul : my_f, my_df, my_fdf
double my_f(const gsl_vector* x, void* params) {
    // Code de la fonction coût
    return 0.0;  // Placeholder
}

void my_df(const gsl_vector* x, void* params, gsl_vector* g) {
    // Code du calcul du gradient
}

void my_fdf(const gsl_vector* x, void* params, double* f, gsl_vector* g) {
    *f = my_f(x, params);
    my_df(x, params, g);
}
*/

/* La fonction f à minimiser */
double my_f(const gsl_vector *v,void *vparams)
{ 
	int min, max, diff_min_max;
	double lambda0, lambda, temp;
 
	Parametres *params=(Parametres*)vparams;
  
	min = params->GetMin();
	max = params->GetMax();
	lambda0 =params->GetLambda();

	diff_min_max = max - min;
	lambda = lambda0 * 1./(diff_min_max*diff_min_max); 

	temp = Fonction_Terme_Regularisation(v,vparams) + lambda * Fonction_Attache_Donnees(v,vparams);

	return temp;
}


/* The gradient of f, df = (df/dx, df/dy). */
void my_df (const gsl_vector *v, void *vparams,  gsl_vector *df)
{
	int min, max, diff_min_max, TailleX, TailleY;
	double  lambda0, lambda;

	Parametres *params=(Parametres*)vparams;

	TailleX = params->GetTailleX();
	TailleY = params->GetTailleY();  
	min = params->GetMin();
	max = params->GetMax();
	lambda0 =params->GetLambda();


	diff_min_max = max - min;
	lambda = lambda0 * 1./(diff_min_max*diff_min_max);

	//Dérivée de l'attache aux données
	gsl_vector *df_temp;
	df_temp = gsl_vector_alloc(TailleX*TailleY);

	Derivee_Attache_Donnees(v,df_temp,vparams);
	gsl_vector_scale(df_temp,lambda);

	Derivee_Terme_Regularisation(v,df,vparams);
   
	gsl_vector_add(df,df_temp); 

	gsl_vector_free(df_temp);
}


/* Compute both f and df together. */
void my_fdf (const gsl_vector *x, void *vparams, double *f, gsl_vector *df) 
{
	*f = my_f(x, vparams); 
	my_df(x, vparams, df);
}

/*
void saveAsTiff(const cv::Mat& mne_min_max, const std::string& filename)
{
    // Assurez-vous que les valeurs sont bien dans la plage [0, 255]
    cv::Mat mne_scaled;
    mne_min_max.convertTo(mne_scaled, CV_8U, 255);  // Convertir en type 8 bits avec échelle

    // Sauvegarder l'image en format TIFF
    if (cv::imwrite(filename, mne_scaled))
    {
        std::cout << "Image sauvegardée avec succès sous le nom : " << filename << std::endl;
    }
    else
    {
        std::cerr << "Erreur lors de la sauvegarde de l'image." << std::endl;
    }
}
*/

void GEA(const cv::Mat& TTIma_MNE, const cv::Mat& TTIma_Masque, const cv::Mat& TTIma_Solut_Init, 
         cv::Mat& TTIma_MNT, const std::string& NOM_norme, float sigma, float lambda, float no_data_ext) 
{
	//std::cout << "Type of TTIma_MNE: " << TTIma_MNE.type() << std::endl;
	
    // Processing image data into vectors...
    //for (int y = 0; y < 5; ++y)
    //{
        //for (int x = 0; x < 5; ++x)
        //{
			//std::cout << " ------- (" << y << "," << x << ") --- " << TTIma_MNE.at<float>(y, x) << std::endl;
		//}
	//}
	
    int tailleX = TTIma_MNE.cols;
    int tailleY = TTIma_MNE.rows;
    // Normalisation des données MNE et Solution Initiale
    double min_val, max_val;
    //cv::minMaxLoc(TTIma_MNE, &min_val, &max_val);
    cv::Mat mask = (TTIma_MNE != no_data_ext);
    cv::minMaxLoc(TTIma_MNE, &min_val, &max_val, nullptr, nullptr, mask);
    cv::Mat mne_min_max = (TTIma_MNE - min_val) / (max_val - min_val);
    cv::Mat TTIma_Solut_Init_Norm = (TTIma_Solut_Init - min_val) / (max_val - min_val);
	//saveAsTiff(mne_min_max, "normalized_mne.tif");
	//saveAsTiff(mne_min_max, "normalized_Solut_Init_Norm .tif");
    TTIma_MNT = cv::Mat(tailleY, tailleX, CV_64F); // Image de sortie

    //// Processing image data into vectors...
    //for (int y = 0; y < 5; ++y)
    //{
        //for (int x = 0; x < 5; ++x)
        //{
			//std::cout << " norm--- (" << y << "," << x << ") --- " << mne_min_max.at<float>(y, x) << std::endl;
		//}
	//}
	
	
    // GSL minimisation - TPoint2D<double> 
    //int count = 0;
    //for (int y = 0; y < TTIma_Masque.rows; ++y)
    //{
        //for (int x = 0; x < TTIma_Masque.cols; ++x)
        //{
			
			
			////std::cout << TTIma_Masque.at<unsigned char>(y, x) << std::endl;
			//if (TTIma_Masque.at<unsigned char>(y, x) == 11)
			//{
				//unsigned char value = TTIma_Masque.at<unsigned char>(y, x);
				//std::cout << "Valeur : " << static_cast<int>(value) << std::endl;
				//count += 1;
			//}
		//}
	//}

//std::cout << "TTIma_Masque.rows >> " << TTIma_Masque.rows << std::endl;
//std::cout << "TTIma_Masque.cols >> " << TTIma_Masque.cols << std::endl;

	//std::cout << "count >> " << count << std::endl ;
	   
    Parametres params(mne_min_max, TTIma_Masque, TPoint2D(min_val, max_val), NOM_norme, sigma, lambda);
    gsl_multimin_function_fdf my_func;
    my_func.n = tailleX * tailleY;
    my_func.f = my_f;
    my_func.df = my_df;
    my_func.fdf = my_fdf;
    my_func.params = &params;

	//std::cout << "Type of TTIma_Solut_Init_Norm: " << TTIma_Solut_Init_Norm.type() << std::endl;
	
    //for (int y = 0; y < 5; ++y)
    //{
        //for (int x = 0; x < 5; ++x)
        //{
			//std::cout << " ------- (" << y << "," << x << ") --- " << TTIma_Solut_Init_Norm.at<float>(y, x) << std::endl;
		//}
	//}
	
    gsl_vector* x = gsl_vector_alloc(tailleX * tailleY);
    for (int j = 0; j < tailleY; ++j) {
        for (int i = 0; i < tailleX; ++i) {
            gsl_vector_set(x, j * tailleX + i, TTIma_Solut_Init_Norm.at<float>(j, i));
        }
    }

    const gsl_multimin_fdfminimizer_type* T = gsl_multimin_fdfminimizer_conjugate_fr;
    gsl_multimin_fdfminimizer* s = gsl_multimin_fdfminimizer_alloc(T, tailleX * tailleY);
    gsl_multimin_fdfminimizer_set(s, &my_func, x, 0.01, 1e-4);

    //std::cout << "GEMO ** avant GSL " << std::endl;

    size_t iter = 0;
    int status;
    do {
        iter++;
        //if (iter % 1000 == 0) std::cout << " iter - " << iter << std::endl ;
        status = gsl_multimin_fdfminimizer_iterate(s);
        if (status) break;
        status = gsl_multimin_test_gradient(s->gradient, 1e-3);
        if (status == GSL_SUCCESS) {
            //std::cout << "Minimum trouvé ! " << status << std::endl;
            break;
        } 
        
    } while (status == GSL_CONTINUE && iter < 30000);

    // Sauvegarde des résultats
    for (int j = 0; j < tailleY; ++j) {
        for (int i = 0; i < tailleX; ++i) {
            double temp = gsl_vector_get(s->x, j * tailleX + i) * (max_val - min_val);
            TTIma_MNT.at<double>(j, i) = temp + min_val;
        }
    }

    gsl_multimin_fdfminimizer_free(s);
    gsl_vector_free(x);
}
