# ThreadMesh Task List

*Last updated: 2026-02-22 (session 2)*

---

## Open Tasks

### PHASE 1 — Project Scaffold
- [x] **T01** Create `pyproject.toml` for pip packaging — COMPLETE 2026-02-21
- [x] **T02** Create directory structure — COMPLETE 2026-02-21
- [x] **T03** Compute backend detection (GPU vs CPU benchmark, 40% RAM cap) — COMPLETE 2026-02-21

### PHASE 2 — I/O Layer
- [x] **T04** STEP import via gmsh/OCCT — centroid → internal coords, T08/T09 baked in — COMPLETE 2026-02-22
- [x] **T05** STL import via meshio — area-weighted normals, all-surface classification — COMPLETE 2026-02-22
- [ ] **T06** Export pipeline via meshio — transform back to user coordinate system on export; support all meshio formats
- [ ] **T07** HDF5 project save/load (`.tmesh`) — geometry blob, mesh data, criteria settings, EQI weights, undo/redo history

### PHASE 3 — Geometry Conformance System
- [x] **T08** Node classification: Interior/Surface/Edge/Corner via gmsh entity dim (baked into T04) — COMPLETE 2026-02-22
- [x] **T09** Surface normal vectors via gmsh OCCT parametric evaluation; STL: area-weighted face normals — COMPLETE 2026-02-22
- [x] **T11** 3D mesh generation: gmsh Frontal-Delaunay + Netgen optimization pass; QThread dropped (gmsh signal restriction — runs synchronous with wait cursor) — COMPLETE 2026-02-22
- [x] **T41** Tape measure tool: vtkCellPicker surface snap; amber spheres + cyan line + billboard distance label; click-3 clears — COMPLETE 2026-02-22
- [ ] **T10** Deviation constraint enforcement: ε = (P_new - P_surface) / P_surface ≤ threshold; per-workbench defaults (Structural 1%, CFD 0.1%); project Newton moves into tangent plane when violated

### PHASE 4 — Mesh Generation
- [ ] **T11** gmsh Frontal-Delaunay initial mesh generation from STEP geometry; target element size input
- [ ] **T12** Element type detection and selection: 2D (tri/quad), 3D (tet/hex), mixed, shell
- [ ] **T13** CFD boundary layer inflation via gmsh; y+ calculator (C_f = 0.026 × Re^(-1/7)); pyramid transition element auto-insertion
- [ ] **T14** Watertight check (CFD workbench) via PyMeshLab before volume meshing

### PHASE 5 — Mesh Repair
- [ ] **T15** PyMeshLab repair pipeline: free edges, duplicate nodes/elements, inverted elements, zero-area faces, T-connections, hole filling, surface normals fix, isotropic remeshing, mesh decimation, curvature analysis, defeaturing

### PHASE 6 — Optimization Engine
- [ ] **T16** Implement Knupp Condition Number metric: Jacobian computation per element, condition number as barrier objective function
- [ ] **T17** Implement Modified Newton iteration with Armijo line search, applied vertex-by-vertex; Numba `@njit(parallel=True)` CPU; `@cuda.jit` GPU
- [ ] **T18** Implement Target-Matrix extension: ideal Jacobian per sample point, node position optimization to match
- [ ] **T19** Implement 7 standard quality metrics: Aspect Ratio, Skewness, Jacobian Ratio, Condition Number, Orthogonal Quality, Warpage, Element Volume Ratio; plus CFD metrics (non-orthogonality, face area ratio)
- [ ] **T20** Implement EQI: weighted composite of all metrics (0-1 per metric, user-adjustable); convergence tracked as vector delta ≤ 1e-4
- [ ] **T21** Optimization driver toggle: EQI mode (composite gradient/Hessian) vs Condition Number mode (pure Knupp)
- [ ] **T22** Iteration control: min 5, max 100, user-adjustable; convergence auto-stop
- [ ] **T23** Jacobian cache: dirty-flag per element; only recompute for elements adjacent to moved vertices; LRU eviction at 40% RAM

### PHASE 7 — Element Selection & Refinement
- [ ] **T24** Element selection modes: click (single + shift-multi), sphere widget (VTK vtkSphereWidget2), box widget (VTK vtkBoxWidget2); visual highlight of selected elements
- [ ] **T25** Selection stats display: total elements (integer), selected elements (integer), % of total
- [ ] **T26** Refinement zone: N user-specified layers expanding outward from selection; fallback to global rebuild if N exceeds available layers
- [ ] **T27** Transition layer stitching: M layers; linear EQI gradient from inner boundary to outer boundary; convergence limit check at both stitch boundaries; fallback to global if M exceeds available

### PHASE 8 — Assembly Proximity Meshing (Structural)
- [ ] **T28** Multi-part session: hold N parts simultaneously in viewport and memory
- [ ] **T29** Contact zone selection UI: seed node selection on Surface A + N adjacent layers + M transition layers; repeat for Surface B; same layer logic as refinement zones (T26/T27)
- [ ] **T30** Interface-class node designation: classify contact zone nodes as Interface-class; build pre-computed node-pair mapping table (Interface_A ↔ Interface_B) before optimization runs
- [ ] **T31** Interface correspondence constraint in Newton loop: per Interface-class node, check both surface deviation threshold AND |Δ node-to-node vector| / local_element_size ≤ 3.5%; project back if either fails; both surfaces optimized simultaneously with co-constraints active
- [ ] **T32** Conforming surface remesh prompt: determine larger node set → prompt user to define N refinement layers + M transition layers for conforming side → run local Knupp optimization with Interface-class constraints
- [ ] **T33** Tied constraint export (no midpoint nodes — solver handles gap interpolation): Interface_A + Interface_B node sets → Abaqus `*TIE`, ANSYS bonded contact, Nastran RBE3
- [ ] **T34** Interface validation report: surface deviation check + 3.5% correspondence check on all interface node pairs; flag failures with achieved deviation values

### PHASE 9 — GUI
- [ ] **T35** Main window: dominant 3D VTK viewport embedded in PySide6 via QVTKRenderWindowInteractor
- [ ] **T36** Workbench selector: Structural / CFD on startup; switchable at any time
- [ ] **T37** Theme: mid-dark grey (#1e1e2e–#2a2a3e), neon cyan/amber/green accents (Alien/80s sci-fi); uniform design language
- [ ] **T38** Top toolbar: Import | Workbench | Measure | Mesh | Shaded/Wireframe | Display Mode | Export | Undo | Redo
- [ ] **T39** Collapsible side panel: EQI weights, metric selector, iteration controls, layer controls, named patches, contact zone controls
- [ ] **T40** Bottom status bar: element count · selected % · EQI score · compute mode (GPU/CPU) · convergence status · stitch boundary delta · interface correspondence delta
- [ ] **T41** Tape measure tool: click-two-points mode + snap-to-geometry mode (vtkCellPicker / vtkPointPicker); distance in model units
- [ ] **T42** Element quality color gradient display: standard FEA scale (green→red); one legend, selectable per metric
- [ ] **T43** Live convergence plot: matplotlib embedded in PySide6; X=iteration, Y=EQI delta; 1e-4 threshold line
- [ ] **T44** Undo/redo: 10-step delta snapshot history

### PHASE 10 — Packaging
- [ ] **T45** `setup.py` / `pyproject.toml` entrypoint, classifiers, AGPL license declaration
- [ ] **T46** Test pip install on Windows, Linux (Ubuntu), macOS
- [ ] **T47** Verify all required packages resolve correctly; document optional GPU install instructions
- [ ] **T48** Upload to PyPI as `threadmesh`

---

## Closed Tasks

- [x] **T00** Define requirements — COMPLETE 2026-02-21
- [x] **T01** pyproject.toml — COMPLETE 2026-02-21
- [x] **T02** Directory structure — COMPLETE 2026-02-21
- [x] **T03** Compute backend detection — COMPLETE 2026-02-21
- [x] **T04** STEP import (gmsh/OCCT) + centroid CS + VTK display — COMPLETE 2026-02-22
- [x] **T05** STL import (meshio) + normals + VTK display — COMPLETE 2026-02-22
- [x] **T08** Node classification (Corner/Edge/Surface/Interior) — COMPLETE 2026-02-22
- [x] **T09** Surface normal assignment via OCCT parametric eval — COMPLETE 2026-02-22
- [x] **T11** 3D mesh generation (gmsh + Netgen pass; synchronous main thread) — COMPLETE 2026-02-22
- [x] **T41** Tape measure tool (vtkCellPicker snap, billboard label) — COMPLETE 2026-02-22

---

## Notes

- Patent clear: Knupp algorithm, Target-Matrix Paradigm, assembly proximity meshing, EQI composite, surface normal conformance
- Patent blocked: mid-surface extraction (Boeing US 10,042,962, expires ~2035)
- All dependencies AGPL-compatible (BSD, MIT, LGPL, GPL)
- AGPL dual-licensing: contributors must sign CLA before PRs accepted
- deal.II excluded: CMake build requirement incompatible with pip packaging
- GPU packages (cupy, pyopencl) are optional; documented in requirements.txt; fail gracefully
