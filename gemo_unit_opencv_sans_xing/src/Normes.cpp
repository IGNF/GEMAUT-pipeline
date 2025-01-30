#include "Normes.h"

//Constructeur et destructeur des différentes normes

Norme::~Norme(){}

NormeHuber::NormeHuber()
{
	m_coef_huber=1.2107;
}
				
NormeHuber::NormeHuber(double CoefHuber)
{
	m_coef_huber = CoefHuber;
}
  
NormeHuber::~NormeHuber(){}




NormeTukey::NormeTukey()
{		m_coef_tukey = 4.6851;		
		m_coef_carre_sur_six = 4.6851 * 4.6851 / 6.;
}
		
NormeTukey::NormeTukey(double CoefTukey)
{
	m_coef_tukey = CoefTukey;
	m_coef_carre_sur_six = CoefTukey * CoefTukey / 6.;
}

NormeTukey::~NormeTukey(){}



	
NormeHuberTukey::NormeHuberTukey()
{
	m_coef_huber = 1.2107;
	m_coef_tukey = 4.6851;
	m_coef_carre_sur_six = 4.6851 * 4.6851 / 6.;
}
				
NormeHuberTukey::NormeHuberTukey(double CoefHuber, double CoefTukey)
{
	m_coef_huber = CoefHuber;
	m_coef_tukey = CoefTukey;
	m_coef_carre_sur_six = CoefTukey * CoefTukey / 6.;
}
  
NormeHuberTukey::~NormeHuberTukey(){}


NormeL2::NormeL2(){}

NormeL2::~NormeL2(){}
