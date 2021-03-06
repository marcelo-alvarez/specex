#ifndef SPECEX_HERMITE__H
#define SPECEX_HERMITE__H

#include <harp.hpp>

namespace specex {
  double HermitePol(const int Degree, const double &x);
  double HermitePolDerivative(const int Degree, const double &x);
  void HermitePols(harp::vector_double& H, const int Degree, const double &x);
  void HermitePolsAndDerivatives(harp::vector_double& H, harp::vector_double& dHdx, const int Degree, const double &x);

}

#endif
