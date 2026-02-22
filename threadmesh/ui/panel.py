# ThreadMesh - Collapsible side panel
# AGPL-3.0-or-later

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, QSlider,
    QDoubleSpinBox, QSpinBox, QFormLayout, QComboBox,
    QScrollArea, QPushButton
)
from PySide6.QtCore import Qt, Signal

from threadmesh.config import (
    WORKBENCH_STRUCTURAL, WORKBENCH_CFD,
    CONVERGENCE_THRESHOLD, ITERATION_MIN, ITERATION_MAX,
    DEVIATION_THRESHOLD_STRUCTURAL, DEVIATION_THRESHOLD_CFD,
    INTERFACE_CORRESPONDENCE_THRESHOLD,
)


class SidePanel(QScrollArea):
    eqi_weights_changed       = Signal(dict)
    iteration_settings_changed = Signal(dict)
    deviation_threshold_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setSpacing(8)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self.setWidget(self._container)

        self._workbench = WORKBENCH_STRUCTURAL
        self._build()

    def _build(self):
        self._clear()
        self._build_mesh_section()
        self._build_eqi_section()
        self._build_iteration_section()
        self._build_conformance_section()
        if self._workbench == WORKBENCH_CFD:
            self._build_cfd_section()
        self._layout.addStretch()

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _build_mesh_section(self):
        group = QGroupBox("Mesh Generation")
        form = QFormLayout(group)
        form.setSpacing(6)

        self._target_size = QDoubleSpinBox()
        self._target_size.setDecimals(3)
        self._target_size.setRange(0.001, 100_000.0)
        self._target_size.setSingleStep(1.0)
        self._target_size.setValue(5.0)
        self._target_size.setToolTip(
            "Target element characteristic length (model units).\n"
            "Use the tape measure tool to gauge feature sizes."
        )
        form.addRow(QLabel("Element size"), self._target_size)

        self._mesh_algo = QComboBox()
        self._mesh_algo.addItem("Delaunay (faster)",  "delaunay")
        self._mesh_algo.addItem("Frontal (quality)", "frontal")
        form.addRow(QLabel("Algorithm"), self._mesh_algo)

        self._layout.addWidget(group)

    # --- Mesh settings getters ---

    def get_target_element_size(self) -> float:
        return self._target_size.value()

    def get_mesh_algorithm(self) -> str:
        return self._mesh_algo.currentData()

    def set_target_element_size(self, size: float):
        """Auto-set element size hint based on model bounding box diagonal."""
        self._target_size.setValue(size)

    def _build_eqi_section(self):
        group = QGroupBox("Element Quality Index")
        form = QFormLayout(group)
        form.setSpacing(6)

        self._eqi_sliders = {}
        metrics = [
            ("Aspect Ratio",    "aspect_ratio"),
            ("Skewness",        "skewness"),
            ("Jacobian Ratio",  "jacobian_ratio"),
            ("Condition No.",   "condition_number"),
            ("Orthogonal",      "orthogonal_quality"),
            ("Warpage",         "warpage"),
            ("Volume Ratio",    "volume_ratio"),
        ]

        # CFD workbench adds extra metrics
        if self._workbench == WORKBENCH_CFD:
            metrics += [
                ("Non-Orthog.",  "non_orthogonality"),
                ("Face Area Ratio", "face_area_ratio"),
            ]

        for label, key in metrics:
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(50)
            slider.setToolTip(f"{label} weight (0–1)")
            self._eqi_sliders[key] = slider
            form.addRow(QLabel(label), slider)

        # Driver mode
        self._driver_combo = QComboBox()
        self._driver_combo.addItem("EQI (physics-specific)", "eqi")
        self._driver_combo.addItem("Condition Number",       "condition_number")
        form.addRow(QLabel("Driver"), self._driver_combo)

        self._layout.addWidget(group)

    def _build_iteration_section(self):
        group = QGroupBox("Iteration Control")
        form = QFormLayout(group)
        form.setSpacing(6)

        self._iter_min = QSpinBox()
        self._iter_min.setRange(1, 50)
        self._iter_min.setValue(ITERATION_MIN)
        form.addRow(QLabel("Min iterations"), self._iter_min)

        self._iter_max = QSpinBox()
        self._iter_max.setRange(10, 500)
        self._iter_max.setValue(ITERATION_MAX)
        form.addRow(QLabel("Max iterations"), self._iter_max)

        self._convergence = QDoubleSpinBox()
        self._convergence.setDecimals(6)
        self._convergence.setRange(1e-8, 1e-2)
        self._convergence.setSingleStep(1e-5)
        self._convergence.setValue(CONVERGENCE_THRESHOLD)
        form.addRow(QLabel("Convergence Δ"), self._convergence)

        self._layout.addWidget(group)

    def _build_conformance_section(self):
        group = QGroupBox("Geometry Conformance")
        form = QFormLayout(group)
        form.setSpacing(6)

        default = (DEVIATION_THRESHOLD_STRUCTURAL
                   if self._workbench == WORKBENCH_STRUCTURAL
                   else DEVIATION_THRESHOLD_CFD)

        self._dev_threshold = QDoubleSpinBox()
        self._dev_threshold.setDecimals(4)
        self._dev_threshold.setRange(0.0001, 0.05)
        self._dev_threshold.setSingleStep(0.001)
        self._dev_threshold.setValue(default)
        self._dev_threshold.setSuffix("  (fraction)")
        form.addRow(QLabel("Surface deviation"), self._dev_threshold)

        self._iface_threshold = QDoubleSpinBox()
        self._iface_threshold.setDecimals(4)
        self._iface_threshold.setRange(0.001, 0.10)
        self._iface_threshold.setSingleStep(0.005)
        self._iface_threshold.setValue(INTERFACE_CORRESPONDENCE_THRESHOLD)
        self._iface_threshold.setSuffix("  (fraction)")
        form.addRow(QLabel("Interface corr."), self._iface_threshold)

        self._layout.addWidget(group)

    def _build_cfd_section(self):
        group = QGroupBox("y+ Calculator")
        form = QFormLayout(group)
        form.setSpacing(6)

        self._yplus_target = QDoubleSpinBox()
        self._yplus_target.setRange(0.1, 300.0)
        self._yplus_target.setValue(1.0)
        form.addRow(QLabel("Target y+"), self._yplus_target)

        self._yplus_velocity = QDoubleSpinBox()
        self._yplus_velocity.setRange(0.001, 1e6)
        self._yplus_velocity.setValue(10.0)
        self._yplus_velocity.setSuffix(" m/s")
        form.addRow(QLabel("Flow velocity"), self._yplus_velocity)

        self._yplus_length = QDoubleSpinBox()
        self._yplus_length.setRange(0.001, 1e4)
        self._yplus_length.setValue(1.0)
        self._yplus_length.setSuffix(" m")
        form.addRow(QLabel("Ref. length"), self._yplus_length)

        self._yplus_density = QDoubleSpinBox()
        self._yplus_density.setRange(0.001, 20000.0)
        self._yplus_density.setValue(1.225)
        self._yplus_density.setSuffix(" kg/m³")
        form.addRow(QLabel("Density"), self._yplus_density)

        self._yplus_viscosity = QDoubleSpinBox()
        self._yplus_viscosity.setDecimals(8)
        self._yplus_viscosity.setRange(1e-8, 1.0)
        self._yplus_viscosity.setValue(1.81e-5)
        self._yplus_viscosity.setSuffix(" Pa·s")
        form.addRow(QLabel("Dyn. viscosity"), self._yplus_viscosity)

        btn_calc = QPushButton("Calculate First Layer Thickness")
        btn_calc.clicked.connect(self._calculate_yplus)
        form.addRow(btn_calc)

        self._yplus_result = QLabel("—")
        self._yplus_result.setObjectName("accent")
        form.addRow(QLabel("First layer Δy"), self._yplus_result)

        self._layout.addWidget(group)

    def _calculate_yplus(self):
        from threadmesh.config import CF_COEFFICIENT, CF_EXPONENT
        yplus    = self._yplus_target.value()
        U        = self._yplus_velocity.value()
        L        = self._yplus_length.value()
        rho      = self._yplus_density.value()
        mu       = self._yplus_viscosity.value()
        nu       = mu / rho
        Re       = U * L / nu
        Cf       = CF_COEFFICIENT * Re ** CF_EXPONENT
        u_tau    = U * (Cf / 2) ** 0.5
        delta_y  = yplus * nu / u_tau
        self._yplus_result.setText(f"{delta_y:.6g} m")

    def set_workbench(self, workbench: str):
        self._workbench = workbench
        self._build()
