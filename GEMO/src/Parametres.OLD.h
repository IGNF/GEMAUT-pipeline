#ifndef _PARAMETRES_
#define _PARAMETRES_

#include <opencv2/opencv.hpp>
#include <vector>
#include <string>  // Assuming TChaine is just a string
#include "Normes.h"
#include "TPoint2D.h"

/**
Contient l'ensemble des paramètres nécessaires à GEA(), l'algorithme de construction d'un MNT.
*/
class Parametres
{
public:
    // Constructor: accepts cv::Mat instead of TTImage
    Parametres(const cv::Mat& TTIma_MNE, const cv::Mat& TTIma_Masque, 
               TPoint2D<double> SortieMinMax, const std::string& NOM_norme, 
               float sigma, float lambda)
        : m_taille{TTIma_MNE.cols, TTIma_MNE.rows},  // Set size from Mat dimensions
          m_SortieMin(static_cast<int>(SortieMinMax.x)), 
          m_SortieMax(static_cast<int>(SortieMinMax.y)), 
          m_sigma(sigma), 
          m_lambda(lambda) 
    {
        // Convert cv::Mat into vectors (formerly PILE)
        m_pil_MNE = std::vector<double>(TTIma_MNE.begin<double>(), TTIma_MNE.end<double>());
        m_pil_Masque = std::vector<unsigned int>(TTIma_Masque.begin<unsigned short>(), TTIma_Masque.end<unsigned short>());
        
        // Here, assume TypeDerive_X and Y are precomputed or handled similarly
        m_pil_Pix_TypeDerive_X = std::vector<int>(m_taille.x * m_taille.y, 0);  // Dummy initialization
        m_pil_Pix_TypeDerive_Y = std::vector<int>(m_taille.x * m_taille.y, 0);  // Dummy initialization

        // Assuming Norme is a class managing the norms
        m_norme = new Norme(NOM_norme);  // Initialize Norme object
    }
    
    // Destructor: clean up if necessary
    ~Parametres() {
        delete m_norme;  // Clean up dynamic allocation
    }

    // Accessor methods (inline for performance)
    inline int GetTailleX() const { return m_taille.x; }
    inline int GetTailleY() const { return m_taille.y; }
    inline int GetMin() const { return m_SortieMin; }
    inline int GetMax() const { return m_SortieMax; }
    inline double GetSigma() const { return m_sigma; }
    inline double GetLambda() const { return m_lambda; }
    
    inline double GetPtMNE(int i) const { return m_pil_MNE[i]; }
    inline unsigned int GetPtMasque(int i) const { return m_pil_Masque[i]; }
    
    inline int GetTypeDeriveX(int i) const { return m_pil_Pix_TypeDerive_X[i]; }
    inline int GetTypeDeriveY(int i) const { return m_pil_Pix_TypeDerive_Y[i]; }
    
    // Norm calculation from the Norme class
    inline double GetNormeDistance(double Val, double Sigma) const { return m_norme->Distance(Val, Sigma); }
    inline double GetNormeDerivee(double Val, double Sigma) const { return m_norme->Derivee(Val, Sigma); }

protected:
    TPoint2D<int> m_taille;  // Image dimensions
    int m_SortieMin;
    int m_SortieMax;
    double m_sigma;
    double m_lambda;
    
    // Replacing PILE with std::vector
    std::vector<double> m_pil_MNE;
    std::vector<unsigned int> m_pil_Masque;
    std::vector<int> m_pil_Pix_TypeDerive_X;
    std::vector<int> m_pil_Pix_TypeDerive_Y;

    Norme* m_norme;  // Pointer to Norme object
};

#endif
