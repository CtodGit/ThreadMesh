# Mathematical References and Acknowledgments

ThreadMesh is built on the published work of the following researchers.
Their contributions form the mathematical foundation of the optimization
engine, mesh generation pipeline, and quality metrics implemented here.

---

## Mesh Quality Optimization

### Patrick M. Knupp — Condition Number Metric & Algebraic Mesh Quality Metrics

The core optimization objective in ThreadMesh — minimizing the condition
number of the element Jacobian matrix — is due to Knupp's foundational work
on algebraic mesh quality.

> Knupp, P. M. (2001).
> **Algebraic mesh quality metrics.**
> *SIAM Journal on Scientific Computing*, 23(1), 193–218.
> https://doi.org/10.1137/S1064827500371499

> Knupp, P. M. (2000).
> **Achieving finite element mesh quality via optimization of the Jacobian
> matrix norm and associated quantities.**
> *International Journal for Numerical Methods in Engineering*, 48(8), 1165–1185.
> https://doi.org/10.1002/(SICI)1097-0207(20000720)48:8<1165::AID-NME940>3.0.CO;2-Y

### Patrick M. Knupp — Target-Matrix Paradigm

The Target-Matrix extension (specifying an ideal Jacobian per sample point
and optimizing node positions to match) is also due to Knupp.

> Knupp, P. M. (2012).
> **Introducing the Target-Matrix Paradigm for mesh optimization via
> node-movement.**
> *Engineering with Computers*, 28(4), 419–429.
> https://doi.org/10.1007/s00366-011-0230-1

---

## Numerical Optimization

### Larry Armijo — Armijo Line Search

The Armijo sufficient-decrease condition used in the modified Newton
iteration to guarantee convergence.

> Armijo, L. (1966).
> **Minimization of functions having Lipschitz continuous first partial
> derivatives.**
> *Pacific Journal of Mathematics*, 16(1), 1–3.
> https://doi.org/10.2140/pjm.1966.16.1

### Newton & Raphson — Newton–Raphson Iteration

The vertex-by-vertex Newton iteration applied per optimization step.

> Newton, I. (1669). *De analysi per aequationes numero terminorum infinitas.*
> (Published 1711.)

> Raphson, J. (1690). *Analysis Aequationum Universalis.*

Modern numerical treatment:

> Nocedal, J. & Wright, S. J. (2006).
> **Numerical Optimization** (2nd ed.).
> Springer.
> https://doi.org/10.1007/978-0-387-40065-5

---

## Mesh Generation

### Boris Delaunay — Delaunay Triangulation

The underlying triangulation criterion used by gmsh's Frontal-Delaunay
surface and volume mesh generators.

> Delaunay, B. (1934).
> **Sur la sphère vide.**
> *Bulletin de l'Académie des Sciences de l'URSS*, Classe des sciences
> mathématiques et naturelles, 7, 793–800.

### Löhner & Parikh — Advancing-Front (Frontal) Method

The frontal mesh generation algorithm available as the "Frontal" option
in ThreadMesh's mesh generation settings.

> Löhner, R. & Parikh, P. (1988).
> **Generation of three-dimensional unstructured grids by the
> advancing-front method.**
> *International Journal for Numerical Methods in Fluids*, 8(10), 1135–1149.
> https://doi.org/10.1002/fld.1650081003

### Christophe Geuzaine & Jean-François Remacle — gmsh

The mesh generation and geometry kernel underlying ThreadMesh's
import, surface meshing, and volume meshing pipelines.

> Geuzaine, C. & Remacle, J.-F. (2009).
> **Gmsh: A 3-D finite element mesh generator with built-in pre- and
> post-processing facilities.**
> *International Journal for Numerical Methods in Engineering*, 79(11), 1309–1331.
> https://doi.org/10.1002/nme.2579

---

## CFD Boundary Layer

### y⁺ First-Layer Thickness Calculator

The flat-plate turbulent skin-friction correlation used in the CFD
workbench y⁺ calculator (C_f = 0.026 × Re^(−1/7)):

> Schlichting, H. & Gersten, K. (2017).
> **Boundary Layer Theory** (10th ed.).
> Springer.
> https://doi.org/10.1007/978-3-662-52919-5

---

## Related Prior Art (Inspiration)

### Mesquite Mesh Quality Improvement Toolkit

The Mesquite project, which pioneered practical implementations of
Knupp's algebraic quality metrics and Target-Matrix methods, served
as a reference architecture. ThreadMesh reimplements these algorithms
independently in Python/NumPy/Numba without using Mesquite code.

> Brewer, M., Diachin, L., Knupp, P., Leurent, T. & Melander, D. (2003).
> **The Mesquite mesh quality improvement toolkit.**
> *Proceedings of the 12th International Meshing Roundtable*, 239–250.
> https://www.osti.gov/biblio/975430
