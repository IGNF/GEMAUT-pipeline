#include "Attache_Donnees.h"


//********************************************
//*****    Fonction_Attache_Donnees    *******
//********************************************
double Fonction_Attache_Donnees(const gsl_vector *v, void *vparams)
{
	int min, max, TailleX, TailleY, min_max;
	double Approx_Attache_aux_donnees, Sigma0, Sigma;

	Parametres *params=(Parametres*)vparams;

	TailleX = params->GetTailleX();
	TailleY = params->GetTailleY();  
	min = params->GetMin();
	max = params->GetMax();
	min_max = max - min;
	Sigma0 = params->GetSigma();


	Sigma =  Sigma0 * 1./min_max;
	Approx_Attache_aux_donnees = 0.;
 
	const double *gsl_ptr = gsl_vector_const_ptr(v, 0);
	
	for (int i=0; i< TailleX*TailleY ; i++, gsl_ptr++)
	{

		if ( params->GetPtMasque(i) == 0)  
		{
			Approx_Attache_aux_donnees += params->GetNormeDistance((*gsl_ptr) - (params->GetPtMNE(i)),Sigma); 
		}//if

	}//for 
 
	return Approx_Attache_aux_donnees; 

}//Fonction_Attache_Donnees



//*******************************************
//*****    Derivee_Attache_Donnees    *******
//*******************************************
void Derivee_Attache_Donnees(const gsl_vector *v, gsl_vector *df, void *vparams)
{
  
	int TailleX, TailleY, min, max, min_max;
	double derivee, Sigma0, Sigma;
  
	Parametres *params=(Parametres*)vparams;

	TailleX = params->GetTailleX();
	TailleY = params->GetTailleY();  
	min = params->GetMin();
	max = params->GetMax();
	min_max = max - min;
	Sigma0 = params->GetSigma();
	Sigma =  Sigma0 * 1./min_max;


  
	const double *gsl_ptr = gsl_vector_const_ptr(v, 0);
	double *df_ptr = gsl_vector_ptr(df, 0);	

	for (int i=0; i< TailleX*TailleY ; i++, gsl_ptr++, df_ptr++)
	{
		if (  params->GetPtMasque(i) != 0)
		{
			derivee = 0;
		}  
		else 
		{
			derivee = params->GetNormeDerivee((*gsl_ptr) - ( params->GetPtMNE(i)),Sigma);
		}//if
		*df_ptr = derivee;
	}//for 
 
}//Derivee_Attache_Donnees

