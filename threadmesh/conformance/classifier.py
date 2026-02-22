# ThreadMesh - Geometry state and node classification
# AGPL-3.0-or-later
#
# GeometryState: central data carrier for all import + mesh data.
# NodeClass: degrees-of-freedom classification assigned at import time.
# Implements T08 (classification) and the data structure used by T09-T34.

import numpy as np
from dataclasses import dataclass, field


class NodeClass:
    """Degrees-of-freedom classification for mesh nodes.

    Assigned at import time from gmsh entity topology (dim 0-3).
    Lower-dimensional entity wins when a node appears in multiple.

    INTERIOR  (3 DOF): free to move in 3D — interior volume nodes
    SURFACE   (2 DOF): constrained to surface tangent plane
    EDGE      (1 DOF): constrained to feature curve tangent
    CORNER    (0 DOF): fixed — geometry vertex point
    INTERFACE (4)    : assembly contact zone; dual-surface constraint
    """
    INTERIOR  = 3
    SURFACE   = 2
    EDGE      = 1
    CORNER    = 0
    INTERFACE = 4


@dataclass
class GeometryState:
    """All geometry and mesh data for one imported part.

    Coordinate convention
    ---------------------
    Internal coords : centroid translated to (0, 0, 0) on import.
                      Used for all optimization math.
    User coords     : internal_coords + origin_offset
                      Restored on export so the user sees their original CS.

    Populated by io/importer.py; consumed by optimize/, conformance/, ui/.
    """

    # Origin
    path: str                       # original file path (re-import on mesh generation)
    file_type: str                  # "step" | "stl"
    origin_offset: np.ndarray       # (3,) float64 — add to internal for user coords

    # Nodes
    node_tags: np.ndarray           # (N,) int64 — gmsh node tags (1-based)
    node_coords: np.ndarray         # (N, 3) float64 — internal coordinate system
    node_class: np.ndarray          # (N,) int8 — NodeClass values
    surface_normals: np.ndarray     # (N, 3) float64 — NaN for non-Surface nodes

    # Surface elements (for display + deviation tracking)
    surf_element_types: list        # list of gmsh element type IDs
    surf_element_tags: list         # per-type: np.ndarray of element tags
    surf_element_node_tags: list    # per-type: np.ndarray of node tag connectivity

    # Volume elements — empty until T11 mesh generation
    vol_element_types: list = field(default_factory=list)
    vol_element_tags: list = field(default_factory=list)
    vol_element_node_tags: list = field(default_factory=list)

    # --- Convenience properties ---

    @property
    def n_nodes(self) -> int:
        return len(self.node_tags)

    @property
    def n_surface_elements(self) -> int:
        return sum(len(t) for t in self.surf_element_tags)

    @property
    def n_volume_elements(self) -> int:
        return sum(len(t) for t in self.vol_element_tags)

    @property
    def n_elements(self) -> int:
        return self.n_volume_elements or self.n_surface_elements

    def to_user_coords(self, internal: np.ndarray) -> np.ndarray:
        """Convert internal → user (original) coordinate system."""
        return internal + self.origin_offset

    def to_internal_coords(self, user: np.ndarray) -> np.ndarray:
        """Convert user → internal coordinate system."""
        return user - self.origin_offset

    def tag_index_map(self) -> np.ndarray:
        """Return a direct-lookup array: tag_to_idx[tag] = array_index.

        Uses 1-based gmsh tags; index 0 of the array is unused (tag 0 invalid).
        Returns -1 for any tag not in node_tags.
        """
        max_tag = int(self.node_tags.max())
        lut = np.full(max_tag + 1, -1, dtype=np.int64)
        lut[self.node_tags] = np.arange(self.n_nodes, dtype=np.int64)
        return lut
