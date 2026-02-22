# Session: 2026-02-21 — Requirements Definition

## Context
Previous session crashed before saving. This session rebuilt all requirements from scratch via conversation with user. All content saved incrementally to REQUIREMENTS.md throughout session.

## Key Decisions Made

### What ThreadMesh Is
- Mesh generator and optimizer only — not a physics preprocessor
- User imports STEP/STL, generates high quality mesh, exports to their solver
- Physics setup (BCs, loads, constraints) done in downstream solver (Abaqus, ANSYS, OpenFOAM, etc.)

### Core Algorithm
- Knupp Condition Number + Modified Newton iteration (implemented natively — no deal.II)
- deal.II removed: Python bindings require CMake build, incompatible with pip packaging
- Numba JIT for performance (@njit parallel CPU, @cuda.jit GPU)
- Two optimization driver modes: EQI (default, physics-specific) or pure Condition Number

### Workbenches (2 only)
- Structural: standard FEA meshing + assembly proximity meshing
- CFD: adds BL inflation, y+ calculator, pyramid transitions, watertight check, non-orthogonality metrics
- Heat transfer removed — same as structural meshing, BC setup in solver

### Geometry Conformance System
- Node classification: Interior (3DOF), Surface (2DOF), Edge (1DOF), Corner (0DOF)
- Unit normal vector assigned to each Surface node via gmsh/OCCT
- Deviation formula: ε = (P_new - P_surface) / P_surface ≤ threshold
- Coordinate system: store user CS on import, work internally (centroid away from origin), export back in user CS
- Thresholds: Structural 1%, CFD 0.1% (user-adjustable)

### Assembly Proximity Meshing (Structural)
- User meshes parts one at a time
- Auto-detect surfaces within proximity tolerance between parts
- Finer mesh drives interface density
- Midpoint interface node set generated, validated against deviation constraint
- Exported as tied constraint (Abaqus *TIE, ANSYS bonded, Nastran RBE3)

### Patent Status
- Knupp condition number + Newton: NO PATENT — published academic work (Sandia/DOE OSTI)
- Target-Matrix Paradigm: NO PATENT — academic paper, Knupp 2012
- Assembly proximity meshing: NO PATENT FOUND — standard FEA practice
- Surface normal constraint conformance: NO PATENT FOUND — our own approach
- EQI weighted composite: NO PATENT FOUND — our own concept
- Mid-surface extraction: PATENTED — US 10,042,962 Boeing (2018, expires ~2035) — EXCLUDED

### AGPL Compatibility — All Packages Confirmed Clear
| Package | License |
|---------|---------|
| VTK | BSD-3-Clause ✓ |
| meshio | MIT ✓ |
| PySide6 | LGPL-3.0 ✓ |
| gmsh | GPL-2.0+ ✓ |
| numpy | BSD-3-Clause ✓ |
| scipy | BSD-3-Clause ✓ |
| numba | BSD-2-Clause ✓ |
| h5py | BSD-3-Clause ✓ |
| matplotlib | PSF/BSD ✓ |
| psutil | BSD-3-Clause ✓ |
| GPUtil | MIT ✓ |
| pynvml | BSD-3-Clause ✓ |
| pyopencl | MIT ✓ |
| cupy | MIT ✓ |
| pymeshlab | LGPL-3.0 ✓ |

## Files Modified This Session
- `REQUIREMENTS.md` — created and built incrementally throughout session
- `requirements.txt` — updated with all pip dependencies
- `.claude/` — converted from file to folder; CLAUDE.md, sessions/, tasks/ created
- `REQUIREMENTS.md` moved to project root

## Status at Session End
Requirements complete. Ready to proceed to architecture and implementation.
Next step: create task list, then begin implementation.
