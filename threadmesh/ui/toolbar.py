# ThreadMesh - Top toolbar
# AGPL-3.0-or-later

from PySide6.QtWidgets import QToolBar, QToolButton, QComboBox, QWidget, QSizePolicy, QLabel
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction

from threadmesh.config import WORKBENCH_STRUCTURAL, WORKBENCH_CFD, COLOR_ACCENT_CYAN


class Toolbar(QToolBar):
    workbench_changed = Signal(str)
    import_requested  = Signal()
    mesh_requested    = Signal()
    export_requested  = Signal()
    undo_requested    = Signal()
    redo_requested    = Signal()
    display_mode_changed = Signal(str)   # "shaded" | "wireframe"
    measure_toggled   = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setFloatable(False)
        self._build()

    def _build(self):
        # Workbench selector
        self.addWidget(QLabel("  Workbench "))
        self._workbench_combo = QComboBox()
        self._workbench_combo.addItem("Structural", WORKBENCH_STRUCTURAL)
        self._workbench_combo.addItem("CFD",        WORKBENCH_CFD)
        self._workbench_combo.setFixedWidth(110)
        self._workbench_combo.currentIndexChanged.connect(self._on_workbench)
        self.addWidget(self._workbench_combo)

        self.addSeparator()

        # Import
        btn_import = QToolButton()
        btn_import.setText("Import")
        btn_import.setToolTip("Import STEP or STL file")
        btn_import.clicked.connect(self.import_requested)
        self.addWidget(btn_import)

        # Measure
        btn_measure = QToolButton()
        btn_measure.setText("⟷ Measure")
        btn_measure.setToolTip("Tape measure tool")
        btn_measure.setCheckable(True)
        btn_measure.toggled.connect(self.measure_toggled)
        self.addWidget(btn_measure)

        self.addSeparator()

        # Mesh
        btn_mesh = QToolButton()
        btn_mesh.setText("▶ Mesh")
        btn_mesh.setToolTip("Generate and optimize mesh")
        btn_mesh.setObjectName("primary")
        btn_mesh.clicked.connect(self.mesh_requested)
        self.addWidget(btn_mesh)

        self.addSeparator()

        # Display mode
        btn_shaded = QToolButton()
        btn_shaded.setText("Shaded")
        btn_shaded.setCheckable(True)
        btn_shaded.setChecked(True)
        btn_shaded.clicked.connect(lambda: self.display_mode_changed.emit("shaded"))
        self.addWidget(btn_shaded)

        btn_wire = QToolButton()
        btn_wire.setText("Wireframe")
        btn_wire.setCheckable(True)
        btn_wire.clicked.connect(lambda: self.display_mode_changed.emit("wireframe"))
        self.addWidget(btn_wire)

        self._display_btns = [btn_shaded, btn_wire]
        for b in self._display_btns:
            b.clicked.connect(lambda _, clicked=b: self._exclusive_display(clicked))

        self.addSeparator()

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(spacer)

        # Undo / Redo
        btn_undo = QToolButton()
        btn_undo.setText("↩ Undo")
        btn_undo.clicked.connect(self.undo_requested)
        self.addWidget(btn_undo)

        btn_redo = QToolButton()
        btn_redo.setText("↪ Redo")
        btn_redo.clicked.connect(self.redo_requested)
        self.addWidget(btn_redo)

        self.addSeparator()

        # Export
        btn_export = QToolButton()
        btn_export.setText("Export ▾")
        btn_export.setToolTip("Export mesh to solver format")
        btn_export.clicked.connect(self.export_requested)
        self.addWidget(btn_export)
        self.addWidget(QLabel("  "))

    def _on_workbench(self, index: int):
        workbench = self._workbench_combo.itemData(index)
        self.workbench_changed.emit(workbench)

    def _exclusive_display(self, active: QToolButton):
        for b in self._display_btns:
            b.setChecked(b is active)

    def set_workbench(self, workbench: str):
        idx = self._workbench_combo.findData(workbench)
        if idx >= 0:
            self._workbench_combo.blockSignals(True)
            self._workbench_combo.setCurrentIndex(idx)
            self._workbench_combo.blockSignals(False)
