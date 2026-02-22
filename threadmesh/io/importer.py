# ThreadMesh - STEP / STL importer
# AGPL-3.0-or-later
#
# Implements T04 (STEP via gmsh/OCCT), T05 (STL via meshio),
# T08 (node classification), T09 (surface normal assignment).
#
# Coordinate system contract
# --------------------------
# On import: centroid translated to internal origin (0,0,0).
# origin_offset stored in GeometryState so export can restore user CS.
# User never sees internal coords.

import numpy as np
from PySide6.QtWidgets import QFileDialog, QMessageBox

from threadmesh.conformance.classifier import GeometryState, NodeClass


SUPPORTED_FILTERS = (
    "Geometry files (*.step *.stp *.stl);;"
    "STEP (*.step *.stp);;"
    "STL (*.stl);;"
    "All files (*)"
)


def import_file(parent=None) -> "GeometryState | None":
    """Show file dialog and import the selected geometry.

    Returns a populated GeometryState on success, None on cancel or error.
    """
    path, _ = QFileDialog.getOpenFileName(
        parent,
        "Import Geometry",
        "",
        SUPPORTED_FILTERS,
    )
    if not path:
        return None

    suffix = path.rsplit(".", 1)[-1].lower()
    try:
        if suffix in ("step", "stp"):
            return _import_step(path, parent)
        elif suffix == "stl":
            return _import_stl(path, parent)
        else:
            QMessageBox.warning(
                parent,
                "Unsupported Format",
                f"Format '.{suffix}' is not supported.\n"
                "Supported: STEP (.step, .stp), STL (.stl)",
            )
            return None
    except Exception as exc:
        QMessageBox.critical(
            parent,
            "Import Error",
            f"Failed to import:\n{path}\n\n{exc}",
        )
        return None


# ---------------------------------------------------------------------------
# STEP import — T04, T08, T09
# ---------------------------------------------------------------------------

def _import_step(path: str, parent=None) -> GeometryState:
    """Import STEP geometry via gmsh/OCCT.

    Steps
    -----
    1. Load via gmsh.model.occ.importShapes (bundles OCCT kernel)
    2. Compute bounding-box centroid → translate to internal origin
    3. Generate a surface mesh for display (Frontal-Delaunay, auto-sized)
    4. Collect all nodes; build fast tag→index lookup
    5. Classify nodes by lowest-dimension entity (Corner > Edge > Surface > Interior)
    6. Assign surface normal vectors via gmsh OCCT surface evaluation
    7. Extract surface elements for VTK display; finalize gmsh
    """
    import gmsh

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.option.setNumber("General.Verbosity", 1)

    try:
        # 1. OCCT import
        gmsh.model.occ.importShapes(path)
        gmsh.model.occ.synchronize()

        # Sanity: confirm we got at least one entity
        if not gmsh.model.getEntities():
            raise ValueError("No geometry entities found in file.")

        # 2. Centroid → internal coordinate system
        xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(-1, -1)
        cx = (xmin + xmax) / 2.0
        cy = (ymin + ymax) / 2.0
        cz = (zmin + zmax) / 2.0
        origin_offset = np.array([cx, cy, cz], dtype=np.float64)

        if not np.allclose(origin_offset, 0.0, atol=1e-12):
            gmsh.model.occ.translate(gmsh.model.getEntities(), -cx, -cy, -cz)
            gmsh.model.occ.synchronize()

        # 3. Surface mesh — sized by curvature, good for display quality
        gmsh.option.setNumber("Mesh.Algorithm", 6)                    # Frontal-Delaunay 2D
        gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 1)
        gmsh.option.setNumber("Mesh.MinimumCirclePoints", 12)         # min points per curve
        gmsh.option.setNumber("Mesh.CharacteristicLengthExtendFromBoundary", 1)
        gmsh.model.mesh.generate(2)

        # 4. Collect nodes
        raw_tags, raw_coords, _ = gmsh.model.mesh.getNodes()
        node_tags   = np.asarray(raw_tags,   dtype=np.int64)
        node_coords = np.asarray(raw_coords, dtype=np.float64).reshape(-1, 3)
        n = len(node_tags)

        # Fast lookup: tag_to_idx[gmsh_tag] = array_index
        max_tag = int(node_tags.max())
        tag_to_idx = np.full(max_tag + 1, -1, dtype=np.int64)
        tag_to_idx[node_tags] = np.arange(n, dtype=np.int64)

        # 5. Node classification — lower-dimensional entity wins
        #    Start everything as INTERIOR; successively override with
        #    SURFACE, then EDGE, then CORNER (each overrides previous).
        node_class = np.full(n, NodeClass.INTERIOR, dtype=np.int8)

        for dim, cls in [
            (2, NodeClass.SURFACE),
            (1, NodeClass.EDGE),
            (0, NodeClass.CORNER),
        ]:
            for _, tag in gmsh.model.getEntities(dim):
                ntags_raw, _, _ = gmsh.model.mesh.getNodes(dim, tag, includeBoundary=False)
                if len(ntags_raw) == 0:
                    continue
                ntags = np.asarray(ntags_raw, dtype=np.int64)
                # Filter to tags we actually have in our lookup
                in_range = ntags[ntags <= max_tag]
                idxs = tag_to_idx[in_range]
                node_class[idxs[idxs >= 0]] = cls

        # 6. Surface normals — OCCT parametric evaluation per surface entity
        #    For each surface entity, getNodes returns (u,v) params per node.
        #    getNormal(tag, [u1,v1,u2,v2,...]) → [nx1,ny1,nz1,nx2,ny2,nz2,...]
        surface_normals = np.full((n, 3), np.nan, dtype=np.float64)

        for _, stag in gmsh.model.getEntities(2):
            ntags_raw, _, params_raw = gmsh.model.mesh.getNodes(
                2, stag, includeBoundary=False, returnParametricCoord=True
            )
            if len(ntags_raw) == 0:
                continue
            ntags  = np.asarray(ntags_raw, dtype=np.int64)
            params = np.asarray(params_raw, dtype=np.float64)  # flat [u,v, u,v, ...]

            try:
                nrm_flat = gmsh.model.getNormal(stag, params.tolist())
                normals  = np.asarray(nrm_flat, dtype=np.float64).reshape(-1, 3)
            except Exception:
                continue  # degenerate surface — skip normals for this patch

            in_range = ntags <= max_tag
            valid_tags = ntags[in_range]
            valid_nrm  = normals[in_range]
            idxs = tag_to_idx[valid_tags]
            good = idxs >= 0
            surface_normals[idxs[good]] = valid_nrm[good]

        # 7. Surface elements (type 2 = tri3, type 3 = quad4)
        raw_stypes, raw_stags, raw_sconn = gmsh.model.mesh.getElements(dim=2)

        return GeometryState(
            path=path,
            file_type="step",
            origin_offset=origin_offset,
            node_tags=node_tags,
            node_coords=node_coords,
            node_class=node_class,
            surface_normals=surface_normals,
            surf_element_types=list(raw_stypes),
            surf_element_tags=[np.asarray(t, dtype=np.int64) for t in raw_stags],
            surf_element_node_tags=[np.asarray(c, dtype=np.int64) for c in raw_sconn],
        )

    finally:
        gmsh.finalize()


# ---------------------------------------------------------------------------
# STL import — T05
# ---------------------------------------------------------------------------

def _import_stl(path: str, parent=None) -> GeometryState:
    """Import STL geometry via meshio.

    STL has no topology (no feature edges, no vertex points), so all nodes
    are classified as SURFACE. Normals are computed as per-vertex averages
    of adjacent face normals (area-weighted).
    """
    import meshio

    mesh = meshio.read(path)
    pts  = np.asarray(mesh.points, dtype=np.float64)

    if pts.shape[0] == 0:
        raise ValueError("STL file contains no vertices.")

    # Centroid → internal coordinates
    centroid = pts.mean(axis=0)
    origin_offset = centroid.copy()
    node_coords = pts - centroid

    n = len(node_coords)
    # gmsh-style 1-based tags for consistency
    node_tags = np.arange(1, n + 1, dtype=np.int64)

    # All STL nodes are surface nodes
    node_class = np.full(n, NodeClass.SURFACE, dtype=np.int8)

    # Collect triangle connectivity (meshio cell type "triangle")
    triangles = None
    for block in mesh.cells:
        if block.type == "triangle":
            triangles = np.asarray(block.data, dtype=np.int64)
            break

    # Compute area-weighted per-vertex normals
    surface_normals = np.full((n, 3), np.nan, dtype=np.float64)
    if triangles is not None and len(triangles) > 0:
        v0 = node_coords[triangles[:, 0]]
        v1 = node_coords[triangles[:, 1]]
        v2 = node_coords[triangles[:, 2]]
        face_nrm = np.cross(v1 - v0, v2 - v0)          # (M, 3) unnormalized = area-weighted
        vertex_nrm = np.zeros((n, 3), dtype=np.float64)
        np.add.at(vertex_nrm, triangles[:, 0], face_nrm)
        np.add.at(vertex_nrm, triangles[:, 1], face_nrm)
        np.add.at(vertex_nrm, triangles[:, 2], face_nrm)
        norms = np.linalg.norm(vertex_nrm, axis=1, keepdims=True)
        norms = np.where(norms > 0, norms, 1.0)
        surface_normals = vertex_nrm / norms

    # Build surf elements in gmsh-style format (type 2 = tri3)
    if triangles is not None and len(triangles) > 0:
        m = len(triangles)
        elem_tags = np.arange(1, m + 1, dtype=np.int64)
        # Convert 0-based meshio indices to 1-based gmsh-style tags
        elem_conn = (triangles + 1).ravel().astype(np.int64)
        surf_types = [2]
        surf_etags = [elem_tags]
        surf_econn = [elem_conn]
    else:
        surf_types, surf_etags, surf_econn = [], [], []

    return GeometryState(
        path=path,
        file_type="stl",
        origin_offset=origin_offset,
        node_tags=node_tags,
        node_coords=node_coords,
        node_class=node_class,
        surface_normals=surface_normals,
        surf_element_types=surf_types,
        surf_element_tags=surf_etags,
        surf_element_node_tags=surf_econn,
    )
