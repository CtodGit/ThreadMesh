# Original Contributions

The following methodologies and formulations are original work by
**Launch Machine, LLC** and are not derived from any single published paper.
They build upon the mathematical foundations credited in `REFERENCES.md`
but represent novel design contributions in their own right.

---

## 1. Element Quality Index (EQI)

A weighted composite quality metric defined as a unified optimization
objective across seven industry-standard element quality measures:

| Metric | Description |
|---|---|
| Aspect Ratio | Ratio of longest to shortest edge |
| Skewness | Deviation of element angles from ideal |
| Jacobian Ratio | Min/max Jacobian determinant ratio |
| Condition Number | Knupp condition number of Jacobian matrix |
| Orthogonal Quality | Dot product of face normal to centroid vector |
| Warpage | Out-of-plane deviation for quad/hex faces |
| Element Volume Ratio | Local volume relative to target volume |

Each metric is user-adjustable on a continuous 0–1 weight scale. The EQI
vector is tracked across iterations; convergence is declared when the
L∞ norm of the delta vector falls below the user-specified threshold.

A dual-driver toggle allows the user to optimize against the full EQI
composite or against pure Condition Number (Knupp) alone — providing
a direct comparison between physics-specific and mathematically
rigorous optimization objectives.

**CFD workbench** extends EQI with two additional metrics:
non-orthogonality (degrees from face normal) and face area ratio,
aligned with OpenFOAM mesh quality requirements.

---

## 2. Assembly Proximity Meshing Workflow

A node-set-based approach for generating conforming mesh interfaces
between surfaces in proximity, designed for FEA pre-processing without
requiring coincident geometry.

**Workflow:**
1. User selects a seed node on Surface A and specifies N adjacent element
   layers. The process is repeated independently on Surface B.
2. The larger of the two node sets drives the mesh density. The smaller
   surface receives locally inserted nodes and a local Knupp re-optimization
   to match density.
3. Both surfaces are co-optimized simultaneously with Interface-class
   constraints active on all contact zone nodes.
4. No midpoint nodes are generated across the gap. Two node sets
   (Interface_A, Interface_B) are exported as a tied constraint
   (Abaqus `*TIE`, ANSYS bonded contact, Nastran RBE3).
   Gap interpolation is delegated to the solver.

The "parent/child" terminology replaces the historically used
"master/slave" designation throughout the codebase and documentation.

---

## 3. Interface Correspondence Threshold

A quantitative conformance criterion for assembly contact zone node pairs:

```
|Δ node-to-node vector| / local_element_size ≤ 3.5%
```

This threshold is more conservative than the Abaqus default (5%) and
is enforced as a hard constraint within the Newton iteration — any
proposed node move that would violate this threshold is projected back
to the feasible set before the step is accepted.

The 3.5% value was selected to produce a tighter tie constraint than
commercial defaults while remaining achievable on curved and non-planar
surface pairs.

---

## 4. Five-Class Node DOF System

A node classification scheme that assigns degrees of freedom based on
topological entity dimension, enforced as hard constraints within the
Modified Newton optimization step:

| Class | DOF | Constraint | Source entity dim |
|---|---|---|---|
| Interior | 3 | None — free in 3D | Volume (dim 3) |
| Surface | 2 | Move in tangent plane only | Surface (dim 2) |
| Edge | 1 | Move along curve tangent only | Curve (dim 1) |
| Corner | 0 | Fixed | Vertex (dim 0) |
| Interface | 1–2 | Surface + correspondence constraint | Contact zone |

Lower-dimensional entities take precedence: a node on a feature edge
is classified Edge, not Surface. Corner nodes are immovable.

Surface and Edge nodes have proposed Newton moves projected into their
respective tangent plane or curve tangent before acceptance, maintaining
geometry conformance throughout the optimization without a separate
projection step.

The Interface class is a fifth type not present in standard node
classification schemes. It carries both a surface deviation constraint
(same as Surface-class) and the inter-surface correspondence constraint
defined in §3 above.

---

## Authorship

All original contributions documented here were conceived and specified
by **Launch Machine, LLC** — a company building precision engineering
tools that commercial incumbents have had decades to build and didn't.

Implementation was carried out under their direction.

© 2026 Launch Machine, LLC. All rights reserved.
This document establishes priority of authorship for the methodologies
described above as of the date of first commit to the ThreadMesh
repository.
