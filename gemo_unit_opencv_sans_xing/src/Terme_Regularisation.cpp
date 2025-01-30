#include "Terme_Regularisation.h"



double Fonction_Terme_Regularisation(const gsl_vector *v, void *vparams)
{ 

	int ipix;
 
	double Approx_derivee_seconde, z0, z1, z2, derivee_partielle;
	int i, j, TailleX, TailleY;
  
	Approx_derivee_seconde = 0.;
  

	Parametres *params=(Parametres*)vparams;

	TailleX = params->GetTailleX();
	TailleY = params->GetTailleY(); 

 	//********************************************
  	//******   Dérivée suivant l'axe des X   *****
  	//********************************************    
	for (j=0;j<TailleY;j++)
	{
		const double *debut = gsl_vector_const_ptr(v,j*TailleX+2);      
		const double *fin = gsl_vector_const_ptr(v,(j+1)*TailleX-1);
		const double *gsl_ptr;
     
		z0 = gsl_vector_get(v,j*TailleX);
		z1 = gsl_vector_get(v,j*TailleX+1);
    
		ipix=j*TailleX+1;
		for (gsl_ptr = debut; gsl_ptr <= fin ; gsl_ptr++, ipix++)
		{
			z2 = *gsl_ptr;

			if(params->GetTypeDeriveX(ipix)>4)
			{
				derivee_partielle =  z0 - 2 * z1 + z2;	
				derivee_partielle *= derivee_partielle; 
				Approx_derivee_seconde += derivee_partielle;
			}
	  
			z0 = z1;
			z1 = z2;
		}//for 

	}//for j


  	//********************************************
  	//******   Dérivée suivant l'axe des Y   *****
  	//********************************************
	for (i=0;i<TailleX;i++)
	{
		const double *gsl_ptr;
		const double *debut = gsl_vector_const_ptr(v,2*TailleX+i);
		const double *fin = gsl_vector_const_ptr(v,(TailleY-1)*TailleX+i);
      
		z0 = gsl_vector_get(v,i);
		z1 = gsl_vector_get(v,TailleX+i);

		ipix=TailleX+i;
		for (gsl_ptr = debut; gsl_ptr <= fin ; gsl_ptr += TailleX, ipix +=TailleX)
		{
			z2 = *gsl_ptr;
	  
			if(params->GetTypeDeriveY(ipix)>4)
			{
				derivee_partielle = z0 - 2 * z1 + z2;
				derivee_partielle *= derivee_partielle;
				Approx_derivee_seconde += derivee_partielle;
			}
			z0 = z1;
			z1 = z2;
		}//for
	}//for i 

	return Approx_derivee_seconde;

}//Fonction_Terme_Regularisation





//**************************************************
//********     Derivee_Derivee_Seconde    **********
//**************************************************
void Derivee_Terme_Regularisation(const gsl_vector *v, gsl_vector *df, void *vparams)
{

	long double temp;
	int i, j, TailleX, TailleY;
	int coef;
	int Type_Derive;
	int ind_m2;
	int ind_m1;
	int ind_1;
	int ind_2;
	int axe=0;


	Parametres *params=(Parametres*)vparams;

	TailleX = params->GetTailleX();
	TailleY = params->GetTailleY(); 

	for (i=0;i<TailleX;i++)
	{
		for(j=0;j<TailleY;j++)
		{
			gsl_vector_set(df,j*TailleX+i,0);
		}//for j
	}//for i

	for(i=0; i<TailleX*TailleY;i++)
	{
		temp=0;
		coef=0;

		if(params->GetTypeDeriveX(i)!=-1)	//Pixel dans la zone à traiter
		{
			for(axe=0; axe<=1; axe++)
			{

				if(axe==0)//axe x
				{
					Type_Derive=params->GetTypeDeriveX(i);
					ind_m2=i-2;
					ind_m1=i-1;
					ind_1=i+1;
					ind_2=i+2;

				}
				else //axe y
				{
					Type_Derive=params->GetTypeDeriveY(i);
					ind_m2=i-2*TailleX;
					ind_m1=i-TailleX;
					ind_1=i+TailleX;
					ind_2=i+2*TailleX;

				}	
	
				switch(Type_Derive) 	//Legende: *:pix traité -:pix voisin |:pix en dehors de la zone
				{
	
					case 0: break;	//	||*||
	
					case 1: break;	//	|-*||
	
					case 2: 	//	--*||
						temp +=
							+2*gsl_vector_get(v,ind_m2)  
							-4*gsl_vector_get(v,ind_m1);
						coef+=2;
						break;
	
					case 3: break;	//	||*-|
	
					case 4: 	//	||*--
						temp +=
							-4*gsl_vector_get(v,ind_1)
							+2*gsl_vector_get(v,ind_2); 
						coef+=2;
						break;
	
					case 5: 	//	--*-|
						temp +=
							+2*gsl_vector_get(v,ind_m2)  
							-8*gsl_vector_get(v,ind_m1)
							-4*gsl_vector_get(v,ind_1);
						coef+=10;
						break;    
	
					case 6: 	//	|-*-|
						temp +=
							-4*gsl_vector_get(v,ind_m1)
							-4*gsl_vector_get(v,ind_1);
						coef+=8;
						break;
	
					case 7: 	//	|-*--
						temp +=
							+2*gsl_vector_get(v,ind_2)
							-4*gsl_vector_get(v,ind_m1)
							-8*gsl_vector_get(v,ind_1);
						coef+=10;
						break;
	
					case 8: 	//	--*--
						temp +=
							+2*gsl_vector_get(v,ind_m2)  
							+2*gsl_vector_get(v,ind_2)
							-8*gsl_vector_get(v,ind_m1)
							-8*gsl_vector_get(v,ind_1);  
						coef+=12;
						break;
	
	
					default: 
						std::cout << "Erreur: Terme de regularisation, Switch default" << std::endl;
						break;
				}//switch

			}//for axe

			temp+=coef*gsl_vector_get(v,i);
		}//if pixel en dehors de la zone
		else	//if pixel en dehors de la zone
		{
			temp=0;
		}//else

		gsl_vector_set(df,i,temp);
	}//for

}//Derivee_Terme_Regularisation





