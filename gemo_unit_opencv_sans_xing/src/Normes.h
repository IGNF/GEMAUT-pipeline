#ifndef _NORMES_
#define _NORMES_

#include <cmath>  // Ajout pour l'utilisation de fabs

//-----------------------------------------------------------------
//--------     LES CLASSES DE NORMES    ---------------------------
//-----------------------------------------------------------------

/////////////////////////////////////////////////////////////////////////////////////////////////////////
/**Classe mère des différentes classes de normes.
Les classes dérivées sont destinées à être utilisées polymorphiquement en étant manipulées via un pointeur vers la classe mère (voir constructeur de la classe Parametres).
La classe mère Norme ne contient donc que les méthodes virtuels qui seront surcharger par ses classes dérivées.
*/
/////////////////////////////////////////////////////////////////////////////////////////////////////////
class Norme
{
	public:
		virtual ~Norme();
		virtual double Distance(double,double) =0;
		virtual double Derivee(double,double) =0;
	
};


////////////////////////
///NORME D'HUBER   
////////////////////////
class NormeHuber : public Norme
{ 
	public:
		

		NormeHuber();	
		NormeHuber(double);
		~NormeHuber();

		inline double Distance(double Val, double Sigma)
		{
			double Distance;
			Val /= Sigma;

			if (fabs(Val)<m_coef_huber)
			{
				Distance = Val * Val / 2;
			} else  {	  
				Distance = m_coef_huber * ( fabs(Val) - (m_coef_huber / 2) );
			}//if (fabs(Val)<m_coef_huber)
      
			return Distance;      
		}
  
		inline double Derivee(double Val, double Sigma)
		{
			double Derivee;
			Val /= Sigma;
      
			if (fabs(Val)<m_coef_huber)
			{
				Derivee = Val;
			} else {
				if (Val<0)
				{
					Derivee = - m_coef_huber;
				} else {
					Derivee = m_coef_huber;
				}
			}//if (fabs(Val)<Coef_Huber)
      
			Derivee /= Sigma;

			return Derivee;
		}

	protected:
		double m_coef_huber;
};



/////////////////////
///NORME DE TUKEY  
/////////////////////
class NormeTukey : public Norme
{
	public:
		
		NormeTukey();
		NormeTukey(double);
		~NormeTukey();

		inline double Distance(double Val, double Sigma)
		{
			double Distance;
			double temp;
			Val /= Sigma;

			if (fabs(Val)<m_coef_tukey)
			{
				temp =  Val / m_coef_tukey;
				temp*= temp;
				temp = 1 - temp;
				temp*= temp * temp;
				temp = 1 - temp;
				Distance = m_coef_carre_sur_six * temp;
			} else  {
				Distance = m_coef_carre_sur_six;
			}//if (fabs(Val)< m_coef_tukey)
    
			return Distance;
		}//inline double Distance

		inline double Derivee(double Val, double Sigma)
		{
			double Derivee;
			double temp;
			Val /= Sigma;

			if (fabs(Val)<m_coef_tukey)
			{
				temp = Val / m_coef_tukey;
				temp*= temp;
				temp = 1 - temp;	  
				temp*= temp;
				Derivee = Val * temp;
			} else {
				Derivee = 0.;
			}//if
    
			Derivee /= Sigma;

			return Derivee;
		}//inline double Derivee
    
	protected:
		double m_coef_tukey;
		double m_coef_carre_sur_six;
};












////////////////////////////////////////
///NORME DISSYMETRIQUE  HUBER / TUKEY
////////////////////////////////////////
class NormeHuberTukey : public Norme
{ 
	public:
		
		NormeHuberTukey();
		NormeHuberTukey(double,double);
  		~NormeHuberTukey();

		inline double Distance(double Val, double Sigma)
		{
			double Distance;
			double temp;
      
			Val /= Sigma;

			if (Val>0)
			{
	  //******************************************************
	  //**************   norme de Huber  *********************
	  //******************************************************
				if ( (fabs(Val)<m_coef_huber))
				{
					Distance = Val * Val / 2;
				} 
				else
				{	  
					Distance = m_coef_huber * ( fabs(Val) - (m_coef_huber / 2) );
				}//if (fabs(Val)<m_coef_huber)
	  
			} else  {
	  //******************************************************
	  //**************   norme de Tukey  *********************
	  //******************************************************
				if (fabs(Val)<m_coef_tukey)
				{
					temp =  Val / m_coef_tukey;
					temp*= temp;
					temp = 1 - temp;
					temp*= temp * temp;
					temp = 1 - temp;
					Distance = m_coef_carre_sur_six * temp;
				} else  {
					Distance = m_coef_carre_sur_six;
				}//if (fabs(Val)<m_coef_tukey)
	  
				return Distance;

			}//if (Val<0)
      
			return Distance;      
		}
  
		inline double Derivee(double Val, double Sigma)
		{
			double Derivee;
			double temp;

			Val /= Sigma;
      
			if (Val>0)
			{
	  //******************************************************
	  //**************   d�riv�e de huber  ********************
	  //******************************************************	 
				if (fabs(Val)<m_coef_huber)
				{
					Derivee = Val;
				} else {
					Derivee =  m_coef_huber;
				}//if (fabs(Val)<m_coef_huber)

			} else {
       	  //******************************************************
	  //**************   d�riv�e de Tukey  ********************
	  //******************************************************
				if (fabs(Val)<m_coef_tukey)
				{
					temp = Val / m_coef_tukey;
					temp*= temp;
					temp = 1 - temp;	  
					temp*= temp;
					Derivee = Val * temp;
				} else {
					Derivee = 0.;
				}//if
	  
			}//if (Val<0)
      
			Derivee /= Sigma;

			return Derivee;
		}

	protected:
		double m_coef_huber;
		double m_coef_tukey;
		double m_coef_carre_sur_six;
};





////////////////////////////////////////
///NORME L2
////////////////////////////////////////
class NormeL2 : public Norme
{
 public:

  NormeL2();
  ~NormeL2();

  inline double Distance(double val, double Sigma)
    {
      return (val * val / 2);
    }

  inline double Derivee(double val, double Sigma)
    {
      return val;
    }

};//NormeL2


#endif
