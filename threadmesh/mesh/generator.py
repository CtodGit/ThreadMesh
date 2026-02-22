# ThreadMesh - 3D mesh generation
# AGPL-3.0-or-later
#
# T11: gmsh Frontal-Delaunay volume meshing from imported STEP geometry.
# Re-imports the STEP (stored in GeometryState.path), applies the same
# centroid translation as the original import, generates a 3D tet mesh,
# runs a Netgen optimization pass, and returns an updated GeometryState.

import numpy as np
from threadmesh.conformance.classifier import GeometryState, NodeClass


def generate_mesh(
    state: GeometryState,
    target_size: float,
    algorithm: str = "delaunay",
) -> GeometryState:
    """Generate a 3D volume mesh from an imported STEP file.

    Parameters
    ----------
    state       : GeometryState from import — .path and .origin_offset reused
    target_size : target element characteristic length (model units, e.g. mm)
    algorithm   : "delaunay"  — faster, good for most solids
                  "frontal"   — higher surface quality, slower

    Returns
    -------
    New GeometryState with vol_element_* populated (plus updated surface elements).

    Raises
    ------
    ValueError  : unsupported file_type
    RuntimeError: gmsh mesh generation failed
    """
    import gmsh

    if state.file_type not in ("step", "stp"):
        raise ValueError(
            f"3D mesh generation requires a STEP file. "
            f"Received file_type='{state.file_type}'. "
            f"STL → volume meshing is tracked as T12."
        )

    algo3d = 1 if algorithm == "delaunay" else 4  # 1=Delaunay, 4=Frontal

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.option.setNumber("General.Verbosity", 1)

    try:
        # 1. Re-import STEP via OCCT (same as original import)
        gmsh.model.occ.importShapes(state.path)
        gmsh.model.occ.synchronize()

        if not gmsh.model.getEntities():
            raise RuntimeError("No geometry entities found when re-importing STEP.")

        # 2. Apply same centroid translation as original import
        cx, cy, cz = state.origin_offset
        if not np.allclose([cx, cy, cz], 0.0, atol=1e-12):
            gmsh.model.occ.translate(gmsh.model.getEntities(), -cx, -cy, -cz)
            gmsh.model.occ.synchronize()

        # 3. Mesh sizing — user target with curvature-aware refinement
        gmsh.option.setNumber("Mesh.CharacteristicLengthMin", target_size * 0.1)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", target_size)
        gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 1)
        gmsh.option.setNumber("Mesh.MinimumCirclePoints", 10)
        gmsh.option.setNumber("Mesh.CharacteristicLengthExtendFromBoundary", 1)
        gmsh.option.setNumber("Mesh.Algorithm",   6)        # 2D: Frontal-Delaunay
        gmsh.option.setNumber("Mesh.Algorithm3D", algo3d)

        # 4. Generate — surface first, then volume
        gmsh.model.mesh.generate(3)

        # 5. Optimization pass (Netgen improves tet quality significantly)
        try:
            gmsh.model.mesh.optimize("Netgen")
        except Exception:
            pass  # Netgen may not be available on all builds — skip silently

        # 6. Collect nodes
        raw_tags, raw_coords, _ = gmsh.model.mesh.getNodes()
        node_tags   = np.asarray(raw_tags,   dtype=np.int64)
        node_coords = np.asarray(raw_coords, dtype=np.float64).reshape(-1, 3)
        n = len(node_tags)

        max_tag = int(node_tags.max())
        tag_to_idx = np.full(max_tag + 1, -1, dtype=np.int64)
        tag_to_idx[node_tags] = np.arange(n, dtype=np.int64)

        # 7. Node classification (same logic as importer — lower dim wins)
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
                in_range = ntags[ntags <= max_tag]
                idxs = tag_to_idx[in_range]
                node_class[idxs[idxs >= 0]] = cls

        # 8. Surface normals via OCCT parametric evaluation
        surface_normals = np.full((n, 3), np.nan, dtype=np.float64)
        for _, stag in gmsh.model.getEntities(2):
            ntags_raw, _, params_raw = gmsh.model.mesh.getNodes(
                2, stag, includeBoundary=False, returnParametricCoord=True
            )
            if len(ntags_raw) == 0:
                continue
            ntags  = np.asarray(ntags_raw, dtype=np.int64)
            params = np.asarray(params_raw, dtype=np.float64)
            try:
                nrm_flat = gmsh.model.getNormal(stag, params.tolist())
                normals  = np.asarray(nrm_flat, dtype=np.float64).reshape(-1, 3)
            except Exception:
                continue
            in_range   = ntags <= max_tag
            valid_tags = ntags[in_range]
            valid_nrm  = normals[in_range]
            idxs = tag_to_idx[valid_tags]
            good = idxs >= 0
            surface_normals[idxs[good]] = valid_nrm[good]

        # 9. Extract surface + volume elements
        surf_types, surf_tags, surf_conn = gmsh.model.mesh.getElements(dim=2)
        vol_types,  vol_tags,  vol_conn  = gmsh.model.mesh.getElements(dim=3)

        if not vol_types or all(len(t) == 0 for t in vol_tags):
            raise RuntimeError(
                "gmsh produced no volume elements. "
                "Check that the geometry is a closed solid (watertight)."
            )

        return GeometryState(
            path=state.path,
            file_type=state.file_type,
            origin_offset=state.origin_offset,
            node_tags=node_tags,
            node_coords=node_coords,
            node_class=node_class,
            surface_normals=surface_normals,
            surf_element_types=list(surf_types),
            surf_element_tags=[np.asarray(t, dtype=np.int64) for t in surf_tags],
            surf_element_node_tags=[np.asarray(c, dtype=np.int64) for c in surf_conn],
            vol_element_types=list(vol_types),
            vol_element_tags=[np.asarray(t, dtype=np.int64) for t in vol_tags],
            vol_element_node_tags=[np.asarray(c, dtype=np.int64) for c in vol_conn],
        )

    finally:
        gmsh.finalize()
