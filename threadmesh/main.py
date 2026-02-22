# ThreadMesh - Entry point
# AGPL-3.0-or-later
#
# Launch: threadmesh            (after pip install)
#         python -m threadmesh.main
#         python main.py        (from project root)

import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QDockWidget, QMessageBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCursor

from threadmesh.ui.theme import apply as apply_theme
from threadmesh.ui.statusbar import StatusBar
from threadmesh.ui.toolbar import Toolbar
from threadmesh.ui.panel import SidePanel
from threadmesh.ui.viewport import Viewport
from threadmesh.compute import get_config, backend_label
from threadmesh.config import WORKBENCH_STRUCTURAL


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ThreadMesh")
        self.setMinimumSize(1280, 800)
        self.resize(1600, 950)

        self._workbench = WORKBENCH_STRUCTURAL
        self._geometry  = None   # current GeometryState | None

        # --- Central viewport ---
        self._viewport = Viewport(self)
        self.setCentralWidget(self._viewport)

        # --- Toolbar ---
        self._toolbar = Toolbar(self)
        self.addToolBar(Qt.TopToolBarArea, self._toolbar)
        self._toolbar.workbench_changed.connect(self._on_workbench_changed)
        self._toolbar.import_requested.connect(self._on_import)
        self._toolbar.mesh_requested.connect(self._on_mesh)
        self._toolbar.export_requested.connect(self._on_export)
        self._toolbar.display_mode_changed.connect(self._viewport.set_display_mode)
        self._toolbar.measure_toggled.connect(self._viewport.set_measure_active)

        # --- Side panel (right dock) ---
        self._panel_dock = QDockWidget("Controls", self)
        self._panel_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self._panel_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable
        )
        self._side_panel = SidePanel(self)
        self._panel_dock.setWidget(self._side_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self._panel_dock)
        self._panel_dock.setMinimumWidth(280)

        # --- Status bar ---
        self._status = StatusBar(self)
        self.setStatusBar(self._status)

        # --- Compute backend detection after event loop starts ---
        QTimer.singleShot(0, self._init_compute)

    # ------------------------------------------------------------------
    # Startup
    # ------------------------------------------------------------------

    def _init_compute(self):
        get_config()
        self._status.set_compute(backend_label())

    # ------------------------------------------------------------------
    # Workbench
    # ------------------------------------------------------------------

    def _on_workbench_changed(self, workbench: str):
        self._workbench = workbench
        self._side_panel.set_workbench(workbench)
        self._toolbar.set_workbench(workbench)

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    def _on_import(self):
        from threadmesh.io.importer import import_file
        state = import_file(self)
        if state is None:
            return

        self._geometry = state

        # Display in viewport
        self._viewport.load_geometry(state)

        # Update status bar
        self._status.set_element_count(state.n_surface_elements)
        self._status.set_eqi(None)
        self._status.set_convergence(None, None)

        # Auto-size hint: 2% of bounding box diagonal → reasonable starting point
        diag = float(np.linalg.norm(
            state.node_coords.max(axis=0) - state.node_coords.min(axis=0)
        ))
        hint = max(0.001, round(diag * 0.02, 3))
        self._side_panel.set_target_element_size(hint)

        # Window title: show filename
        import os
        fname = os.path.basename(state.path)
        self.setWindowTitle(f"ThreadMesh — {fname}")

    # ------------------------------------------------------------------
    # Mesh generation (T11)
    # ------------------------------------------------------------------

    def _on_mesh(self):
        if self._geometry is None:
            QMessageBox.information(self, "No Geometry", "Import a STEP or STL file first.")
            return

        target_size = self._side_panel.get_target_element_size()
        algorithm   = self._side_panel.get_mesh_algorithm()

        # gmsh.initialize() calls signal.signal() internally — Python restricts
        # that to the main thread only, so mesh generation must run here.
        # Show a wait cursor so the user knows work is happening.
        self._toolbar.setEnabled(False)
        self._status.showMessage(
            f"Generating mesh  (element size {target_size:.3g}, {algorithm})…"
        )
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()  # flush status bar / cursor update

        try:
            from threadmesh.mesh.generator import generate_mesh
            state = generate_mesh(self._geometry, target_size, algorithm)
        except Exception as exc:
            QApplication.restoreOverrideCursor()
            self._toolbar.setEnabled(True)
            self._status.clearMessage()
            QMessageBox.critical(self, "Mesh Generation Failed", str(exc))
            return

        QApplication.restoreOverrideCursor()
        self._toolbar.setEnabled(True)
        self._status.clearMessage()

        self._geometry = state
        self._viewport.load_mesh(state)
        self._status.set_element_count(state.n_volume_elements)
        self._status.set_eqi(None)
        self._status.set_convergence(None, None)

    # ------------------------------------------------------------------
    # Export (T06)
    # ------------------------------------------------------------------

    def _on_export(self):
        pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ThreadMesh")
    app.setApplicationVersion("0.1.0")
    apply_theme(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
