#ifndef _GEA_
#define _GEA_

#include <gsl/gsl_errno.h>
#include <gsl/gsl_fft_complex.h>
#include <gsl/gsl_complex.h>
#include <gsl/gsl_multimin.h>
#include <gsl/gsl_blas.h>

#include "Attache_Donnees.h"
#include "Terme_Regularisation.h"

/**
This function should return the result f(x,params) for argument x and parameters params.
http://www.gnu.org/software/gsl/manual/html_node/Providing-a-function-to-minimize.html
*/
double my_f(const gsl_vector *v, void *vparams);

/**
This function should store the n-dimensional gradient g_i = d f(x,params) / d x_i in the vector g for argument x and parameters params, returning an appropriate error code if the function cannot be computed.
http://www.gnu.org/software/gsl/manual/html_node/Providing-a-function-to-minimize.html
*/
void my_df(const gsl_vector *v, void *vparams,  gsl_vector *df);

/**
This function should set the values of the f and g as above, for arguments x and parameters params. This function provides an optimization of the separate functions for f(x) and g(x)—it is always faster to compute the function and its derivative at the same time.
size_t n
    the dimension of the system, i.e. the number of components of the vectors x.
void * params
    a pointer to the parameters of the function.
http://www.gnu.org/software/gsl/manual/html_node/Providing-a-function-to-minimize.html
*/
void my_fdf (const gsl_vector *x, void *vparams , double *f, gsl_vector *df);

void GEA(const cv::Mat& TTIma_MNE, const cv::Mat& TTIma_Masque, const cv::Mat& TTIma_Solut_Init, cv::Mat& TTIma_MNT, const std::string& NOM_norme, float sigma, float lambda, float no_data_ext);

#endif


