# ThreadMesh Requirements

*Last updated: 2026-02-21*

---

## Overview

ThreadMesh is a pip-installable Python mesh optimization tool with a full graphical user interface. It targets engineers who need higher-quality meshes than those produced by commercial tools (Abaqus, ANSYS, Altair, CATIA, Pro/E). It runs on Windows, Linux, and macOS.

---

## Goals

- Produce measurably higher-quality FEA meshes than commercial meshers via rigorous mathematical optimization
- Full GUI — no CLI knowledge required
- Export to all major FEA formats via meshio
- Distributed as AGPL open source; dual-licensed commercially for companies that cannot comply with copyleft
- Pip-installable: `pip install threadmesh` → `threadmesh`

---

## Core Algorithm

### Knupp Condition Number Optimization + Modified Newton Iteration

Implemented natively in Python/NumPy/Numba. Based on Patrick Knupp's published framework (Sandia National Labs) — no licensing exposure, mathematical methods are not copyrightable.

- **Quality metric**: Condition number of the Jacobian of the mapping from reference element → physical element. Value of 1.0 = perfect; approaching ∞ = degenerate/inverted.
- **Optimizer**: Modified Newton iteration with Armijo line search, applied locally vertex-by-vertex. Barrier nature of condition number prevents element inversion.
- **Target-Matrix extension** (from Mesquite): specify an ideal Jacobian at each sample point; optimize node positions to match. Enables size and alignment control, not just shape.
- **Performance**: inner loop JIT-compiled via Numba `@njit(parallel=True)` on CPU; `@cuda.jit` on NVIDIA GPU.

**References**:
- Knupp, P. — *Achieving FE Mesh Quality via Optimization of the Jacobian Matrix Norm* (Parts I & II, 2000)
- Mesquite / Trilinos — https://trilinos.github.io/mesquite.html

---

## Workbench System

User selects a workbench on startup (or switches at any time). Two workbenches only — ThreadMesh is a mesh generator/optimizer, not a physics preprocessor. Physics setup (BCs, loads, constraints) is done in the downstream solver. Core tools are available in both workbenches.

### Workbench: Structural (FEA)
Additional tools beyond core:
- Named surface patches (element sets, node sets) — written into export for solver BC assignment
- Shell element support
- Assembly proximity meshing (see Assembly Meshing section)
- Interface node set generation for tied constraints
- EQI defaults weighted toward aspect ratio, Jacobian ratio, condition number
- Export: Abaqus (`.inp`), ANSYS (`.cdb`), Altair/Nastran (`.fem`, `.bdf`), CATIA (`.med`), Pro/E (`.bdf`), VTK, STL, all meshio formats

### Workbench: CFD
Additional tools beyond core:
- **y+ Calculator** — input: target y+, flow velocity, reference length, fluid density, dynamic viscosity → output: recommended first layer thickness. Flat-plate turbulent approximation: C_f = 0.026 × Re^(-1/7). No external dependency.
- **Boundary layer inflation** — prismatic structured layers at wall surfaces; first layer thickness informed by y+ calculator; growth rate and layer count user-defined
- **Pyramid transition elements** — auto-generated at BL prism / interior tet interface
- **Watertight check** — blocking error if geometry not fully closed before volume meshing
- **Surface normals check / fix** — detects and corrects inverted normals via PyMeshLab
- **CFD-specific quality metrics** (added to metric selector alongside 7 standard):
  - Max non-orthogonality angle (OpenFOAM limit: <70°, ideal <40°)
  - Face area ratio between adjacent cells
- Named surface patches — written into export for solver patch identification
- EQI defaults weighted toward skewness, orthogonal quality, condition number
- Export: Fluent (`.msh`), CGNS (`.cgns`), OpenFOAM (via Fluent `.msh`), all meshio formats

### Shared Core (Both Workbenches)
- Import (STEP, STL, all meshio formats)
- 3D viewport (pan, zoom, rotate, shaded/wireframe)
- Measurement tool (tape measure, snap to geometry)
- Mesh generation (gmsh Frontal-Delaunay)
- Element selection (click, sphere, box)
- Refinement zones + transition layer stitching
- Knupp optimization + EQI
- Convergence plot
- Mesh repair (PyMeshLab)
- Undo / redo (10 steps)
- Project save / load (`.tmesh`)

---

## Geometry Conformance System

Ensures mesh nodes remain on or within tolerance of the original STEP surface geometry during and after optimization.

### Coordinate System Handling
- On import: read and store user's original coordinate system (transformation matrix)
- Internally: translate geometry so bounding box centroid sits at a safe distance from origin (prevents near-zero division in deviation formula)
- On export: transform all node coordinates back to user's original coordinate system
- User never sees internal coordinate system; exported mesh matches original CAD coordinates exactly

### Node Classification
On import, every node is classified and tagged:

| Class | DOF | Constraint |
|-------|-----|-----------|
| Interior | 3 | Free movement in XYZ |
| Surface | 2 | Tangential slide on surface patch; normal deviation limited |
| Edge | 1 | Movement along STEP curve only |
| Corner | 0 | Fixed — no movement permitted |
| **Interface** | **1–2** | **Tangential slide on own surface + surface deviation threshold + interface correspondence constraint with paired node on opposing surface** |

Classification performed using gmsh's OpenCASCADE (OCCT) API — no additional CAD kernel dependency needed.

### Surface Normal Assignment
- On import, each Surface-class node is assigned a unit normal vector orthogonal to its STEP surface at its UV parameter position
- Normal vectors computed via gmsh/OCCT surface evaluation
- Stored per-node; used to decompose proposed Newton moves into tangential (allowed) and normal (tolerance-checked) components

### Deviation Tolerance Formula
For each Surface-class node after a proposed move:

```
ε = (P_new - P_surface) / P_surface  ≤  threshold
```

Where P_surface is the node's original surface position in internal coordinates (safe distance from origin — no division instability).

| Workbench | Default threshold | User-adjustable |
|-----------|-----------------|----------------|
| Structural | 1.0% | Yes |
| CFD | 0.1% | Yes |

- Edge nodes: threshold / 10 (tighter — sharp edges are physically critical)
- Corner nodes: fixed, no movement

If proposed move violates threshold: project move back to tangent plane, retry. If still violating after projection: accept best achieved position, flag node in repair report.

### Interface Correspondence Constraint
For Interface-class nodes, two independent checks per Newton iteration — both must pass before a move is accepted:

| Check | Formula | Default | Basis |
|-------|---------|---------|-------|
| Surface deviation | ε = (P_new - P_surface) / P_surface | 1% Structural, 0.1% CFD | ThreadMesh conformance system |
| Interface correspondence | \|Δ node-to-node vector\| / local element size | **3.5%** | Conservative of Abaqus 5% standard (user-adjustable) |

- Interface correspondence constraint is pre-computed before optimization: a node-pair mapping table (Interface_A ↔ Interface_B) built from user's contact zone selection
- Newton loop reads constraint table per interface node on every iteration
- If correspondence check fails: project move back to maintain pairing; if still failing after projection: accept best achieved, flag in repair report
- Both surfaces' contact zones optimized simultaneously in the same Newton loop — interface nodes on both sides co-constrain each other in real time

---

## Assembly Proximity Meshing (Structural Workbench)

Enables multi-part assemblies to be meshed one part at a time with user-controlled interface conformance.

### Contact Zone Selection Workflow
1. User selects a seed node on Surface A (most critical contact point)
2. User expands by N layers of adjacent nodes outward — same layer logic as refinement zones
3. User defines M transition layers for stitching contact zone to surrounding mesh on Surface A
4. User repeats steps 1–3 for Surface B
5. ThreadMesh determines which surface has the larger node set — that surface drives interface density
6. Smaller surface gets nodes inserted to match larger surface's density in the contact zone
7. User prompted: "Surface B requires local remesh to match Surface A density. Define refinement and transition layers for the conforming region." — user defines N and M for the conforming side
8. Local Knupp optimization runs on both contact + transition zones simultaneously with Interface-class constraints active
9. Both surfaces validated against deviation threshold and 3.5% correspondence tolerance
10. Final node sets written to export as tied constraint

### Export Format
- Interface_A node set + Interface_B node set written to export
- Solver handles geometric interpolation across gap — no midpoint nodes generated (avoids geometric inaccuracy on curved surfaces)
- Tie constraint format:
  - Abaqus: `*TIE`
  - ANSYS: bonded contact definition
  - Nastran: RBE3

### Conformance Validation
- All interface nodes on each surface: surface deviation threshold check
- All interface node pairs: 3.5% correspondence tolerance check
- Inserted nodes on conforming surface: both checks required before finalizing
- Failed nodes flagged in repair report with achieved deviation values

---

## PyMeshLab Feature Set

All filters applied to surface meshes. Volume mesh repair handled via gmsh. PyMeshLab license: LGPL-3.0 ✓

| Feature | When used |
|---------|-----------|
| Topology check | On import — detect non-manifold, free edges, self-intersections |
| Mesh repair | Pre-optimization — fix free edges, duplicate nodes/elements, inverted elements, zero-area faces, T-connections |
| Hole filling | Pre-optimization — close gaps in surface mesh |
| Surface normals check / fix | CFD workbench — ensure consistent outward normals |
| Mesh decimation / simplification | On demand — reduce element count while preserving shape |
| Isotropic remeshing | Pre-optimization — uniform element size distribution |
| Mesh-level defeaturing | On demand — remove small mesh features below user-defined threshold |
| Curvature analysis | Quality display — surface curvature as additional mesh insight |
| Watertight verification | CFD workbench — confirm fully closed surface before volume meshing |

---

## Functional Requirements

### Workflow (in order)

1. **Workbench selection** — User selects FEA, CFD, or Heat Transfer on startup; can switch at any time
2. **Import** — User loads a STEP or STL file
3. **3D Viewer** — Pan, zoom, rotate geometry in 3D space (2D and 3D geometry supported)
3. **Measurement tool** — Tape measure icon; click two points or snap to geometry (edge, vertex, face) to measure feature size; distance shown in model units
4. **Target element size** — User sets target element size based on measurement; optimizer fills geometry with as many unit-size elements as possible
5. **Criteria** — Default criteria pre-loaded (7 metrics); user can adjust weights before meshing
6. **Mesh** — User presses Mesh; Gmsh Frontal-Delaunay generates initial mesh; Knupp optimization runs immediately after
7. **Element types** — 2D or 3D; quads, tet, hex, or mixed as determined by geometry
8. **Display** — Mesh overlaid on geometry; shaded or wireframe toggle
9. **Element quality coloring** — Standard FEA color gradient (green=good → red=bad); one legend, selectable per metric
10. **Element selection** — User selects elements to refine (see Selection Methods below); selected elements highlight visually
11. **Selection stats** — Displayed near Mesh button at all times:
    - Total elements in model (integer)
    - Selected elements (integer)
    - Selected as % of total model elements (pre-refinement count)
12. **Refinement layers** — User specifies N additional layers to include in the refinement zone:
    - Layer 1 = all elements sharing a face/edge with any selected element
    - Each subsequent layer expands outward from the previous
    - Defaults to global rebuild if N exceeds available layers
13. **Transition layers** — User specifies M transition layers for stitching (default: 1, no upper limit):
    - Sits between the refinement zone and the untouched mesh
    - Defaults to global rebuild if M exceeds available layers
    - See Transition Layer Stitching below for gradient logic
14. **Criteria adjustment** — Adjustable at any point; triggers re-optimization
15. **Optimization loop** — Runs Knupp/Newton iterations; tracks EQI vector delta; stops automatically at convergence (Δ ≤ 1e-4)
16. **Convergence display** — Live embedded plot during optimization:
    - X-axis: iteration number
    - Y-axis: rate of change of EQI vector delta
    - Convergence threshold (1e-4) marked as horizontal line
17. **Export** — User selects format from dropdown; meshio handles conversion

---

### Element Selection Methods

Three modes, all selectable from toolbar:

1. **Click select** — Single click selects one element; shift-click adds to selection
2. **Sphere select** — User places a sphere in 3D space and adjusts diameter; all elements inside are selected (VTK sphere widget)
3. **Box/cube select** — User places a box in 3D space and adjusts dimensions; all elements inside are selected (VTK box widget)

Selected elements highlight with a distinct color overlay in the viewport. Selection is always visible regardless of active display mode (shaded or wireframe).

---

### Transition Layer Stitching

The transition layer set bridges the refined zone and the untouched mesh via a **linear quality gradient**:

- **Inner boundary quality** = EQI of the outermost refinement layer (the layer adjacent to transition)
- **Outer boundary quality** = EQI of the innermost untouched layer (the layer adjacent to transition on the other side)
- **Gradient** = linear interpolation of target EQI across all M transition layers, from inner boundary to outer boundary
- Each transition layer is optimized to match its linearly interpolated target EQI

**Convergence limit at stitch boundaries**:
- At the inner stitch (transition ↔ refined zone): convergence check; if quality cannot be matched within iteration limits, accept best achieved and continue — no infinite loop
- At the outer stitch (transition ↔ untouched mesh): same convergence check
- Both stitch boundaries report their final achieved quality delta to the user in the status bar

---

## Element Quality Metrics (7 industry standard)

| # | Metric | Role |
|---|--------|------|
| 1 | Aspect Ratio | Shape elongation |
| 2 | Skewness | Angular deviation from ideal |
| 3 | Jacobian Ratio (min scaled) | Local invertibility |
| 4 | Condition Number | Core optimization metric (Knupp) |
| 5 | Orthogonal Quality | Face/edge perpendicularity |
| 6 | Warpage | Out-of-plane deviation |
| 7 | Element Volume Ratio | Size consistency |

---

## Optimization Driver Mode

User-selectable toggle (default: EQI):

| Mode | Behavior |
|------|----------|
| **EQI (default)** | Weighted composite of all 7 metrics drives the Newton objective function. Composite gradient and Hessian computed from weighted sum. User's physics-specific priorities directly affect node positions. |
| **Condition Number** | Pure Knupp condition number drives Newton optimization. EQI still displayed and tracked for convergence but does not affect node movement. Fastest, most mathematically stable. |

Both modes use the same Modified Newton + Armijo line search iteration loop. EQI mode is the differentiator vs. commercial tools.

---

## Element Quality Index (EQI)

- Composite of all 7 metrics
- Each metric weighted 0–1, user-adjustable
- Convergence tracked as norm of delta between current EQI array and previous EQI array
- Optimization stops when Δ ≤ 1e-4

## Iteration Control

| Setting | Default | User-adjustable |
|---------|---------|----------------|
| Minimum iterations | 5 | Yes |
| Maximum iterations | 100 | Yes |
| Convergence threshold | 1e-4 | Yes |

- Optimizer always runs at least the minimum iterations regardless of early convergence
- Stops at maximum iterations even if not fully converged
- Convergence plot shows all iterations; threshold line visible throughout

---

## UI / UX

### Theme
- Mid-dark grey background (`#1e1e2e` – `#2a2a3e` range) — not pure black
- Neon accents: cyan, amber, green — Alien (1979) / 80s sci-fi aesthetic
- Polished, slick, uniform design language throughout
- Comparable to modern dark-mode IDEs but with personality

### Layout
- Single window; dominant 3D viewport
- Collapsible side panel: criteria weights, layer controls, EQI breakdown
- Top toolbar: Import | Measure | Mesh | Shaded/Wireframe | Export | Undo | Redo
- Bottom status bar: element count · EQI score · compute mode (GPU/CPU) · convergence status

### Undo / Redo
- 10-step history
- Covers: refinement zone selections, criteria changes, optimization runs, layer additions

---

## Project Save / Load

- Format: HDF5, single `.tmesh` file
- Contains:
  - Original STEP geometry (binary blob)
  - Full mesh (elements, nodes, connectivity)
  - All criteria settings and EQI weights
  - Undo/redo history (up to 10 states)
- Load restores full session state exactly

---

## Export Formats

All formats meshio supports are available. Priority targets:

| Application | Format |
|-------------|--------|
| Abaqus | `.inp` |
| ANSYS | `.cdb` |
| Altair HyperMesh / OptiStruct | `.fem` (Nastran) |
| CATIA | `.med` (MED/Salome) |
| Pro/E (Creo) | `.bdf` (Nastran) |
| Generic | `.vtk`, `.stl`, `.msh`, and all other meshio formats |

---

## Dependencies

### Core (all AGPL-compatible)

| Package | License | Role |
|---------|---------|------|
| VTK | BSD-3-Clause | 3D rendering and visualization pipeline |
| meshio | MIT | Mesh I/O across all supported formats |
| PySide6 | LGPL-3.0 | GUI framework (Qt6) |
| gmsh | GPL-2.0+ | Initial mesh generation (Frontal-Delaunay) |
| numpy | BSD-3-Clause | Core numerical arrays |
| scipy | BSD-3-Clause | Spatial routines, supporting optimization math |
| numba | BSD-2-Clause | JIT compilation of inner optimization loop; CPU SIMD + CUDA GPU targeting |
| pymeshlab | LGPL-3.0 | Topology check on import; mesh repair (free edges, duplicate nodes, inverted elements, etc.) |
| h5py | BSD-3-Clause | HDF5 project file format |
| matplotlib | PSF/BSD | Embedded live convergence plot |
| psutil | BSD-3-Clause | CPU core count and RAM monitoring |

### GPU (optional, imported gracefully — no error if absent)

| Package | License | Role |
|---------|---------|------|
| cupy | MIT | CUDA array operations (NVIDIA) |
| pyopencl | MIT | OpenCL cross-vendor GPU (AMD, Intel) |
| GPUtil | MIT | NVIDIA GPU detection |
| pynvml | BSD-3-Clause | NVIDIA management library bindings |

### Note on deal.II
Originally specified but removed. Python bindings require CMake build-from-source — incompatible with pip packaging. Algorithm implemented natively instead.

---

## Non-Functional Requirements

### Compute Acceleration
- On startup: autodetect and benchmark GPU vs CPU on a synthetic workload
- **GPU faster**: use Numba `@cuda.jit` + CuPy (NVIDIA) or PyOpenCL (AMD/Intel)
- **GPU absent or slower**: use n-1 CPU cores; cap RAM at 40% of system RAM
- **macOS**: OpenCL deprecated (10.14+), CUDA unavailable — silently falls back to CPU, no import errors

### Scale
- 100 elements → 10,000,000 elements
- UI must remain interactive across full range

### Platform
- Windows, Linux (Ubuntu, Debian, and derivatives), macOS
- `pip install threadmesh` → `threadmesh` to launch

---

## Licensing Model

- **Open source**: AGPL-3.0-or-later (full source public)
- **Dual license**: companies that cannot comply with AGPL copyleft purchase a commercial license
- All copyright retained by original author
- Contributors must sign a CLA (Contributor License Agreement) to preserve dual-licensing rights
- Precedent: MySQL, Qt, MongoDB

---

## Import

User performs geometry cleanup externally before importing. ThreadMesh accepts clean geometry.

### Supported Import Formats
- **STEP** (`.step`, `.stp`) — primary format for solid geometry
- **STL** (`.stl`) — surface geometry
- All other mesh formats meshio supports

### On Import: Topology Check
- Automatic lightweight check via PyMeshLab (LGPL-3.0 ✓)
- Detects: non-manifold geometry, free edges, duplicate nodes, self-intersections
- Reports issues with severity (warning vs. blocking error)
- Does not attempt full geometry repair — user expected to fix in source CAD tool

---

## Element Types

- **2D geometry**: triangles, quads, mixed
- **3D geometry**: tet, hex, mixed
- **Shell elements**: fully supported — surface mesh in 3D space for thin-walled structures (sheet metal, plastics, composites). Knupp condition number optimization applies natively to 2D tri/quad elements in 3D space.

---

## Geometry Preprocessing (Pre-Mesh)

### Mesh Repair
- Runs automatically before optimization; user reviews and approves
- Via PyMeshLab (LGPL-3.0 ✓):
  - Free edges
  - Duplicate nodes (merged within tolerance)
  - Duplicate elements
  - Inverted elements (negative Jacobian)
  - Zero-area / zero-volume elements
  - T-connections and non-conforming interfaces
- Repair report: what was found, fixed, and what needs manual attention

### Named Selections / Groups
- User creates named element and node sets in viewport (select elements → assign name)
- Exported in target solver's native format:
  - Abaqus: `*ELSET` / `*NSET`
  - ANSYS: component definitions
  - Altair/Nastran: `SET` cards
- Required for boundary condition application in downstream solvers

### CFD Boundary Layer Inflation
- Defined in CFD Workbench section above
- Generated via gmsh inflation algorithm; pyramid transition elements auto-inserted at BL/interior interface

---

## Robustness

### Error Handling
- All operations wrapped with descriptive, user-facing error messages (no raw Python tracebacks shown to user)
- Geometry import failures: report specific STEP issue, suggest geometry cleanup
- Meshing failures: report cause (degenerate geometry, insufficient space for target element size), offer fallback options
- Optimization failures: report convergence status per zone, continue with best result rather than crashing
- Stitch boundary failures: report achieved quality delta, accept best and continue
- GPU initialization failures: silently fall back to CPU, notify user in status bar

### Caching
- STEP geometry parsed and cached on import; not re-parsed on subsequent operations
- Jacobian matrices cached per element between Newton iterations (only recomputed for vertices that moved)
- EQI metric values cached per element; only invalidated for elements adjacent to moved vertices
- Undo/redo states stored as delta snapshots (not full mesh copies) to minimize memory footprint
- Cache evicted when RAM usage approaches 40% limit; LRU eviction policy

---

## Out of Scope (v1)

- Solver / FEA simulation (ThreadMesh generates and optimizes meshes only)
- Physics setup: boundary conditions, loads, material assignment — done in downstream solver
- CAD modeling or parametric geometry editing
- Structured block topology meshing
- Mid-surface extraction — **PATENT BLOCKED**: US Patent 10,042,962 held by Boeing (issued 2018, expires ~2035). Do not implement.
- Automatic contact type detection (proximity meshing IS in v1; contact type classification is not)
- Heat transfer workbench — thermal meshing uses Structural workbench; thermal BC setup done in solver
- Mesh morphing — planned v2
- AI-assisted workflows — planned v2
- Scripting / batch mode — planned v2
