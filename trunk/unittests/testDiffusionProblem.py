## @package unittests.testDiffusionProblem
#  Runs a diffusion problem and compares to exact solution.

# add source directory to module search path
import sys
sys.path.append('../src')

from math import sqrt, sinh, cosh
from scipy.integrate import quad # adaptive quadrature function
import unittest

from mesh import Mesh
from crossXInterface import ConstantCrossSection
from radiationSolveSS import radiationSolveSS
from plotUtilities import plotScalarFlux, makeContinuousXPoints
from radUtilities import computeScalarFlux, extractAngularFluxes
from integrationUtilities import computeL1ErrorLD
from balanceChecker import BalanceChecker
from radBC import RadBC

## Derived unittest class to run a diffusion problem and compare to exact solution.
#
class TestDiffusionProblem(unittest.TestCase):
   def setUp(self):
      pass
   def tearDown(self):
      pass
   def test_DiffusionProblem(self):

      # number of elements
      n_elems = 50
      # mesh
      xL = 0.0             # left boundary of domain
      xR = 3.0             # right boundary of domain
      mesh = Mesh(n_elems,xR)
   
      # physics data
      sig_a = 0.25         # absorption cross section
      sig_s = 0.75         # scattering cross section
      sig_t = sig_s+sig_a  # total cross section
      D = 1.0/(3*sig_t)    # diffusion coefficient
      L = sqrt(D/sig_a)    # diffusion length
      Q = 1.0              # isotropic source
      rad_BC = RadBC(mesh, "dirichlet", psi_left=0.0, psi_right=0.0)
   
      # cross sections
      cross_sects = [(ConstantCrossSection(sig_s,sig_t),ConstantCrossSection(sig_s,sig_t))
         for i in xrange(n_elems)]
      # sources
      Q_iso  = [(0.5*Q) for i in xrange(mesh.n_elems*4)]
   
      # compute LD solution
      rad = radiationSolveSS(mesh,
                             cross_sects,
                             Q_iso,
                             rad_BC=rad_BC)

      # get continuous x-points
      xlist = makeContinuousXPoints(mesh)
   
      # function for exact scalar flux solution
      def exactScalarFlux(x):
         A = 2.4084787907
         B = -2.7957606046
         return A*sinh(x/L)+B*cosh(x/L)+Q*L*L/D
   
      # compute exact scalar flux solution at each x-point
      scalar_flux_exact = [exactScalarFlux(x) for x in xlist]

      # plot solutions
      if __name__ == '__main__':
         plotScalarFlux(mesh,rad.psim,rad.psip,scalar_flux_exact=scalar_flux_exact)
   
      # compute L1 error
      L1_error = computeL1ErrorLD(mesh,rad.phi,exactScalarFlux)
   
      # compute L1 norm of exact solution to be used as normalization constant
      L1_norm_exact = quad(exactScalarFlux, xL, xR)[0]

      # compute relative L1 error
      L1_relative_error = L1_error / L1_norm_exact

      # check that L1 error is small
      n_decimal_places = 3
      self.assertAlmostEqual(L1_relative_error,0.0,n_decimal_places)

      # check balance
      if __name__ == '__main__':
         bal = BalanceChecker(mesh, problem_type='rad_only', timestepper=None, dt=None)
         bal.computeSSRadBalance(0.0, 0.0, rad, sig_a, 0.5*Q)


# run main function from unittest module
if __name__ == '__main__':
   unittest.main()

