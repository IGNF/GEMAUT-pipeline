#ifndef _TERME_REGULARISATION_
#define _TERME_REGULARISATION_

#include"Parametres.h"

#include <gsl/gsl_errno.h>
#include <gsl/gsl_fft_complex.h>
#include <gsl/gsl_complex.h>
#include <gsl/gsl_multimin.h>
#include <gsl/gsl_blas.h>

/**
Cette fonction fournie le terme de régularisation basée sur le gradient de notre surface MNE
*/
double Fonction_Terme_Regularisation(const gsl_vector *v, void *vparams);

/**
Cette fonction fournie le terme de régularisation basée sur la dérivée du gradient de notre surface MNE
*/
void Derivee_Terme_Regularisation(const gsl_vector *v, gsl_vector *df, void *vparams);

#endif




