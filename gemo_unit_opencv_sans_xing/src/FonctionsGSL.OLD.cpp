#include "FonctionsGSL.h"


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


