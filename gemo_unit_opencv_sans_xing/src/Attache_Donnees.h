#ifndef _ATTACHE_DONNEES_
#define _ATTACHE_DONNEES_

#include"Parametres.h"

#include <gsl/gsl_errno.h>
#include <gsl/gsl_fft_complex.h>
#include <gsl/gsl_complex.h>
#include <gsl/gsl_multimin.h>
#include <gsl/gsl_blas.h>

/**
Détermine le terme d'attache aux données de manière à filtrer les points indésirables.

Le terme est obtenu à l'aide d'une norme définie dans l'argument *vparams qui pointe sur un objet de la classe Parametres (voir aussi Normes.h)
*/
double Fonction_Attache_Donnees(const gsl_vector *v, void *vparams);

/**
Détermine le terme d'attache aux données dérivées de manière à filtrer les points indésirables.

Le terme est obtenu à l'aide d'une norme définie dans l'argument *vparams qui pointe sur un objet de la classe Parametres (voir aussi Normes.h)
*/
void Derivee_Attache_Donnees(const gsl_vector *v, gsl_vector *df, void *vparams);

#endif

