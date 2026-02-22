# ThreadMesh - Status bar
# AGPL-3.0-or-later

from PySide6.QtWidgets import QStatusBar, QLabel
from PySide6.QtCore import Qt
from threadmesh.config import COLOR_ACCENT_CYAN, COLOR_ACCENT_AMBER, COLOR_ACCENT_GREEN, COLOR_TEXT_DIM


class StatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizeGripEnabled(False)

        self._elements      = QLabel("Elements: —")
        self._selected      = QLabel("Selected: —")
        self._eqi           = QLabel("EQI: —")
        self._compute       = QLabel("Compute: —")
        self._convergence   = QLabel("Convergence: —")
        self._interface     = QLabel("")

        for label in [self._elements, self._selected, self._eqi,
                      self._compute, self._convergence, self._interface]:
            self.addPermanentWidget(label)

    def set_element_count(self, total: int):
        self._elements.setText(f"Elements: {total:,}")

    def set_selection(self, selected: int, total: int):
        if total > 0:
            pct = selected / total * 100
            self._selected.setText(f"Selected: {selected:,} ({pct:.1f}%)")
        else:
            self._selected.setText("Selected: —")

    def set_eqi(self, value: float | None):
        if value is None:
            self._eqi.setText("EQI: —")
        else:
            self._eqi.setText(f"EQI: {value:.4f}")

    def set_compute(self, label: str):
        self._compute.setText(f"Compute: {label}")

    def set_convergence(self, delta: float | None, iteration: int | None):
        if delta is None:
            self._convergence.setText("Convergence: —")
        else:
            self._convergence.setText(f"Iter {iteration} · Δ {delta:.2e}")

    def set_interface_delta(self, delta: float | None):
        if delta is None:
            self._interface.setText("")
        else:
            self._interface.setText(f"Interface Δ: {delta:.2e}")
