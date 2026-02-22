# ThreadMesh - 3D VTK viewport embedded in PySide6
# AGPL-3.0-or-later

import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

from threadmesh.ui.measure import MeasureTool

try:
    import vtk
    from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
    from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
    _VTK_AVAILABLE = True
except ImportError:
    _VTK_AVAILABLE = False


# gmsh surface element type IDs → (nodes_per_element, vtk_cell_type)
_GMSH_SURF_TYPES = {
    2: (3, None),   # tri3  — VTK_TRIANGLE (5)
    3: (4, None),   # quad4 — VTK_QUAD (9)
}


class Viewport(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        if _VTK_AVAILABLE:
            self._build_vtk()
        else:
            self._build_fallback()

    def _build_vtk(self):
        self._vtk_widget = QVTKRenderWindowInteractor(self)
        self._layout.addWidget(self._vtk_widget)

        self._renderer = vtk.vtkRenderer()
        self._renderer.SetBackground(0.118, 0.118, 0.180)   # COLOR_BG_DARK
        self._renderer.GradientBackgroundOn()
        self._renderer.SetBackground2(0.165, 0.165, 0.243)  # COLOR_BG_MID

        self._render_window = self._vtk_widget.GetRenderWindow()
        self._render_window.AddRenderer(self._renderer)

        self._interactor = self._render_window.GetInteractor()
        style = vtk.vtkInteractorStyleTrackballCamera()
        self._interactor.SetInteractorStyle(style)

        self._vtk_widget.Initialize()
        self._vtk_widget.Start()

        self._measure_tool = MeasureTool(
            self._renderer, self._render_window, self._interactor
        )

    def _build_fallback(self):
        label = QLabel("VTK not available.\nInstall vtk: pip install vtk")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #ff4444; font-size: 16px;")
        self._layout.addWidget(label)
        self._measure_tool = MeasureTool(None, None, None)  # no-op stub

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------

    def set_measure_active(self, active: bool) -> None:
        """Enable or disable the tape measure tool."""
        if _VTK_AVAILABLE:
            self._measure_tool.set_active(active)

    def get_renderer(self):
        return self._renderer if _VTK_AVAILABLE else None

    def get_render_window(self):
        return self._render_window if _VTK_AVAILABLE else None

    def get_interactor(self):
        return self._interactor if _VTK_AVAILABLE else None

    # ------------------------------------------------------------------
    # Geometry / mesh display
    # ------------------------------------------------------------------

    def load_geometry(self, state) -> None:
        """Display surface geometry from a GeometryState.

        Called after STEP/STL import. Renders the surface mesh in the
        neon-cyan theme with smooth normals and edge overlay.

        state : GeometryState from threadmesh.conformance.classifier
        """
        if not _VTK_AVAILABLE:
            return

        poly = self._build_surface_polydata(state)
        if poly is None:
            return

        # Compute smooth normals for shading
        nrm = vtk.vtkPolyDataNormals()
        nrm.SetInputData(poly)
        nrm.ComputePointNormalsOn()
        nrm.ComputeCellNormalsOff()
        nrm.ConsistencyOn()
        nrm.SplittingOff()          # keep smooth shading across seams
        nrm.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(nrm.GetOutputPort())
        mapper.ScalarVisibilityOff()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        prop = actor.GetProperty()
        prop.SetColor(0.22, 0.52, 0.82)       # steel-blue body
        prop.SetSpecular(0.35)
        prop.SetSpecularPower(40)
        prop.SetAmbient(0.18)
        prop.SetDiffuse(0.82)
        prop.EdgeVisibilityOn()
        prop.SetEdgeColor(0.0, 0.96, 1.0)     # neon-cyan edges
        prop.SetLineWidth(0.6)

        self._measure_tool.clear()
        self._renderer.RemoveAllViewProps()
        self._renderer.AddActor(actor)
        self._renderer.ResetCamera()
        self.render()

    def load_mesh(self, state) -> None:
        """Display optimized mesh from a GeometryState with volume elements.

        Falls back to surface display if no volume elements are present.
        """
        if not _VTK_AVAILABLE:
            return

        if state.n_volume_elements == 0:
            self.load_geometry(state)
            return

        # Volume mesh display: extract surface faces via vtkGeometryFilter
        ug = self._build_unstructured_grid(state)
        if ug is None:
            return

        surface_filter = vtk.vtkGeometryFilter()
        surface_filter.SetInputData(ug)
        surface_filter.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(surface_filter.GetOutputPort())
        mapper.ScalarVisibilityOff()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        prop = actor.GetProperty()
        prop.SetColor(0.22, 0.52, 0.82)
        prop.SetSpecular(0.30)
        prop.SetSpecularPower(30)
        prop.EdgeVisibilityOn()
        prop.SetEdgeColor(0.0, 0.96, 1.0)
        prop.SetLineWidth(0.5)

        self._measure_tool.clear()
        self._renderer.RemoveAllViewProps()
        self._renderer.AddActor(actor)
        self._renderer.ResetCamera()
        self.render()

    # ------------------------------------------------------------------
    # VTK data builders
    # ------------------------------------------------------------------

    def _build_surface_polydata(self, state) -> "vtk.vtkPolyData | None":
        """Convert GeometryState surface elements → vtkPolyData.

        Handles gmsh element types 2 (tri3) and 3 (quad4).
        Uses numpy vectorized cell-array construction for speed.
        """
        # Tag → array-index lookup
        lut = state.tag_index_map()
        max_tag = len(lut) - 1

        tris  = []   # list of (N,3) index arrays
        quads = []   # list of (N,4) index arrays

        for etype, _, econn in zip(
            state.surf_element_types,
            state.surf_element_tags,
            state.surf_element_node_tags,
        ):
            if etype not in _GMSH_SURF_TYPES:
                continue
            npe = _GMSH_SURF_TYPES[etype][0]
            n_elem = len(econn) // npe
            conn = econn.reshape(n_elem, npe)

            # Clamp to valid range before LUT lookup
            valid_rows = np.all((conn > 0) & (conn <= max_tag), axis=1)
            conn = conn[valid_rows]
            idx = lut[conn]

            # Drop any element referencing an unknown node
            valid_idx = np.all(idx >= 0, axis=1)
            idx = idx[valid_idx]

            if etype == 2:
                tris.append(idx)
            elif etype == 3:
                quads.append(idx)

        if not tris and not quads:
            return None

        vtk_pts = vtk.vtkPoints()
        vtk_pts.SetData(numpy_to_vtk(state.node_coords.astype(np.float64), deep=True))

        cells = vtk.vtkCellArray()
        n_cells = 0

        def _append_cells(idx_list, npe):
            nonlocal n_cells
            if not idx_list:
                return
            all_idx = np.vstack(idx_list)          # (M, npe)
            m = len(all_idx)
            # VTK legacy cell format: [npe, i0, i1, ..., npe, i0, i1, ...]
            flat = np.empty(m * (npe + 1), dtype=np.int64)
            flat[0::npe + 1] = npe
            for j in range(npe):
                flat[j + 1::npe + 1] = all_idx[:, j]
            cells.SetCells(
                n_cells + m,
                numpy_to_vtkIdTypeArray(flat, deep=True),
            )
            n_cells += m

        # Build tris, then quads
        if tris:
            all_tri = np.vstack(tris)
            m = len(all_tri)
            flat = np.empty(m * 4, dtype=np.int64)
            flat[0::4] = 3
            flat[1::4] = all_tri[:, 0]
            flat[2::4] = all_tri[:, 1]
            flat[3::4] = all_tri[:, 2]
            cells.SetCells(m, numpy_to_vtkIdTypeArray(flat, deep=True))
            n_cells += m

        if quads:
            all_quad = np.vstack(quads)
            m = len(all_quad)
            flat = np.empty(m * 5, dtype=np.int64)
            flat[0::5] = 4
            flat[1::5] = all_quad[:, 0]
            flat[2::5] = all_quad[:, 1]
            flat[3::5] = all_quad[:, 2]
            flat[4::5] = all_quad[:, 3]
            # Quads go into a second pass — append to existing cell array
            # For mixed, use vtkPolyData with separate SetPolys call
            # Simple: just tessellate quads → 2 tris each
            tri_a = np.column_stack([all_quad[:, 0], all_quad[:, 1], all_quad[:, 2]])
            tri_b = np.column_stack([all_quad[:, 0], all_quad[:, 2], all_quad[:, 3]])
            extra = np.vstack([tri_a, tri_b])
            m2 = len(extra)
            flat2 = np.empty(m2 * 4, dtype=np.int64)
            flat2[0::4] = 3
            flat2[1::4] = extra[:, 0]
            flat2[2::4] = extra[:, 1]
            flat2[3::4] = extra[:, 2]
            # Merge with tris
            if tris:
                merged_m = n_cells + m2
                # Rebuild full cell array merging existing tris + quad tris
                all_tri_full = np.vstack(tris)
                tri_flat = np.empty(len(all_tri_full) * 4, dtype=np.int64)
                tri_flat[0::4] = 3
                tri_flat[1::4] = all_tri_full[:, 0]
                tri_flat[2::4] = all_tri_full[:, 1]
                tri_flat[3::4] = all_tri_full[:, 2]
                merged_flat = np.concatenate([tri_flat, flat2])
                cells.SetCells(merged_m, numpy_to_vtkIdTypeArray(merged_flat, deep=True))
            else:
                cells.SetCells(m2, numpy_to_vtkIdTypeArray(flat2, deep=True))

        poly = vtk.vtkPolyData()
        poly.SetPoints(vtk_pts)
        poly.SetPolys(cells)
        return poly

    def _build_unstructured_grid(self, state) -> "vtk.vtkUnstructuredGrid | None":
        """Convert GeometryState volume elements → vtkUnstructuredGrid (T11+)."""
        # gmsh → VTK cell type mapping
        gmsh_to_vtk = {
            4:  vtk.VTK_TETRA,          # tet4
            5:  vtk.VTK_HEXAHEDRON,     # hex8
            6:  vtk.VTK_WEDGE,          # prism6
            7:  vtk.VTK_PYRAMID,        # pyr5
            11: vtk.VTK_QUADRATIC_TETRA, # tet10
        }
        lut = state.tag_index_map()
        max_tag = len(lut) - 1

        vtk_pts = vtk.vtkPoints()
        vtk_pts.SetData(numpy_to_vtk(state.node_coords.astype(np.float64), deep=True))

        ug = vtk.vtkUnstructuredGrid()
        ug.SetPoints(vtk_pts)

        for etype, _, econn in zip(
            state.vol_element_types,
            state.vol_element_tags,
            state.vol_element_node_tags,
        ):
            if etype not in gmsh_to_vtk:
                continue
            vtk_type = gmsh_to_vtk[etype]
            npe_map = {4: 4, 5: 8, 6: 6, 7: 5, 11: 10}
            npe = npe_map[etype]
            n_elem = len(econn) // npe
            conn = econn.reshape(n_elem, npe)
            valid = np.all((conn > 0) & (conn <= max_tag), axis=1)
            conn = conn[valid]
            idx = lut[conn]
            valid2 = np.all(idx >= 0, axis=1)
            idx = idx[valid2]

            for row in idx:
                cell = vtk.vtkIdList()
                for node_id in row:
                    cell.InsertNextId(int(node_id))
                ug.InsertNextCell(vtk_type, cell)

        return ug if ug.GetNumberOfCells() > 0 else None

    # ------------------------------------------------------------------
    # Viewport controls
    # ------------------------------------------------------------------

    def render(self):
        if _VTK_AVAILABLE:
            self._render_window.Render()

    def set_display_mode(self, mode: str):
        if not _VTK_AVAILABLE:
            return
        actors = self._renderer.GetActors()
        actors.InitTraversal()
        actor = actors.GetNextActor()
        while actor:
            prop = actor.GetProperty()
            if mode == "wireframe":
                prop.SetRepresentationToWireframe()
            else:
                prop.SetRepresentationToSurface()
            actor = actors.GetNextActor()
        self.render()

    def reset_camera(self):
        if _VTK_AVAILABLE:
            self._renderer.ResetCamera()
            self.render()

    def clear(self):
        if _VTK_AVAILABLE:
            self._measure_tool.clear()
            self._renderer.RemoveAllViewProps()
            self.render()
