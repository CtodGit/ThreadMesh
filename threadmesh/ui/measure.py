# ThreadMesh - Tape measure tool
# AGPL-3.0-or-later
#
# T41: Click two points on model geometry; displays a dimensioned
# line annotation with distance in model units.
#
# Interaction
# -----------
# - Click 1 : place first endpoint (amber sphere, snapped to surface)
# - Click 2 : place second endpoint → draw line + distance label
# - Click 3+ : clear and start a new measurement
# - Clicks in empty space do NOT consume the event — camera still rotates
#
# Uses vtkCellPicker (surface snap) with a high-priority observer so the
# trackball camera only sees clicks that miss the geometry.

import math

try:
    import vtk
    _VTK_AVAILABLE = True
except ImportError:
    _VTK_AVAILABLE = False


class MeasureTool:
    """3D tape measure integrated into the VTK viewport."""

    _POINT_COLOR  = (1.0, 0.70, 0.0)   # amber endpoints
    _LINE_COLOR   = (0.0, 0.95, 1.0)   # neon cyan line
    _TEXT_COLOR   = (0.0, 0.95, 1.0)
    _LINE_WIDTH   = 2.0
    _OBS_PRIORITY = 10.0               # > default 0; aborts camera on hit

    def __init__(self, renderer, render_window, interactor):
        self._renderer     = renderer
        self._render_window = render_window
        self._interactor   = interactor
        self._active       = False
        self._points       = []   # list of (x, y, z) tuples, max 2
        self._actors       = []   # VTK actors to remove on clear
        self._obs_id       = None

        if _VTK_AVAILABLE:
            self._picker = vtk.vtkCellPicker()
            self._picker.SetTolerance(0.005)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_active(self, active: bool) -> None:
        if not _VTK_AVAILABLE:
            return

        if active and not self._active:
            self._obs_id = self._interactor.AddObserver(
                "LeftButtonPressEvent",
                self._on_left_press,
                self._OBS_PRIORITY,
            )
        elif not active and self._active:
            if self._obs_id is not None:
                self._interactor.RemoveObserver(self._obs_id)
                self._obs_id = None
            self.clear()

        self._active = active

    def clear(self) -> None:
        """Remove all measurement actors and reset state."""
        if not _VTK_AVAILABLE:
            return
        for actor in self._actors:
            self._renderer.RemoveActor(actor)
        self._actors.clear()
        self._points.clear()
        self._render_window.Render()

    def get_distance(self) -> float | None:
        """Return the last measured distance, or None if < 2 points placed."""
        if len(self._points) < 2:
            return None
        p1, p2 = self._points[0], self._points[1]
        return math.dist(p1, p2)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_left_press(self, obj, event) -> None:
        x, y = obj.GetEventPosition()
        self._picker.Pick(x, y, 0, self._renderer)

        if self._picker.GetCellId() < 0:
            # Missed geometry — pass event through so camera can rotate
            return

        # Hit geometry — place measurement point.
        # No need to abort: trackball camera only rotates on click+drag,
        # not a bare click, so both can coexist safely.
        pt = tuple(self._picker.GetPickPosition())

        if len(self._points) >= 2:
            # Third click → clear previous measurement, start fresh
            self.clear()

        self._points.append(pt)
        self._add_endpoint_actor(pt)

        if len(self._points) == 2:
            self._add_line_and_label()

        self._render_window.Render()

    # --- Actor builders ---

    def _add_endpoint_actor(self, pt: tuple) -> None:
        radius = self._scene_scale() * 0.006

        sphere = vtk.vtkSphereSource()
        sphere.SetCenter(*pt)
        sphere.SetRadius(radius)
        sphere.SetPhiResolution(10)
        sphere.SetThetaResolution(10)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphere.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*self._POINT_COLOR)
        actor.GetProperty().LightingOff()

        self._renderer.AddActor(actor)
        self._actors.append(actor)

    def _add_line_and_label(self) -> None:
        p1, p2 = self._points[0], self._points[1]
        dist   = math.dist(p1, p2)
        mid    = tuple((p1[i] + p2[i]) / 2 for i in range(3))

        # --- Measurement line ---
        line = vtk.vtkLineSource()
        line.SetPoint1(*p1)
        line.SetPoint2(*p2)

        line_mapper = vtk.vtkPolyDataMapper()
        line_mapper.SetInputConnection(line.GetOutputPort())

        line_actor = vtk.vtkActor()
        line_actor.SetMapper(line_mapper)
        line_actor.GetProperty().SetColor(*self._LINE_COLOR)
        line_actor.GetProperty().SetLineWidth(self._LINE_WIDTH)
        line_actor.GetProperty().LightingOff()

        self._renderer.AddActor(line_actor)
        self._actors.append(line_actor)

        # --- Distance label (billboard — always faces camera) ---
        label = vtk.vtkBillboardTextActor3D()
        label.SetInput(f"  {dist:.4g}")
        label.SetPosition(*mid)

        tp = label.GetTextProperty()
        tp.SetColor(*self._TEXT_COLOR)
        tp.SetFontSize(16)
        tp.BoldOn()
        tp.SetBackgroundColor(0.08, 0.08, 0.14)
        tp.SetBackgroundOpacity(0.75)

        self._renderer.AddActor(label)
        self._actors.append(label)

    def _scene_scale(self) -> float:
        """Estimate scene size for proportional sphere radius."""
        bounds = self._renderer.ComputeVisiblePropBounds()
        if bounds[0] > bounds[1]:
            return 1.0
        dx = bounds[1] - bounds[0]
        dy = bounds[3] - bounds[2]
        dz = bounds[5] - bounds[4]
        return math.sqrt(dx * dx + dy * dy + dz * dz)
