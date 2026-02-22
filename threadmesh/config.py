# ThreadMesh - Global configuration and constants
# AGPL-3.0-or-later

# --- Workbenches ---
WORKBENCH_STRUCTURAL = "structural"
WORKBENCH_CFD = "cfd"

# --- Geometry conformance thresholds ---
# ε = (P_new - P_surface) / P_surface ≤ threshold
DEVIATION_THRESHOLD_STRUCTURAL = 0.01       # 1.0%
DEVIATION_THRESHOLD_CFD        = 0.001      # 0.1%
DEVIATION_EDGE_FACTOR          = 0.1        # edge nodes: threshold / 10

# --- Interface correspondence threshold ---
# |Δ node-to-node vector| / local_element_size ≤ threshold
INTERFACE_CORRESPONDENCE_THRESHOLD = 0.035  # 3.5%

# --- Optimization convergence ---
CONVERGENCE_THRESHOLD = 1e-4
ITERATION_MIN         = 5
ITERATION_MAX         = 100

# --- Compute resource limits ---
RAM_MAX_FRACTION  = 0.40    # max 40% of system RAM
CPU_RESERVE_CORES = 1       # always leave 1 core free

# --- Assembly proximity detection ---
PROXIMITY_TOLERANCE_FACTOR = 0.01   # 1% of smallest target element size

# --- Project file ---
PROJECT_FILE_EXTENSION = ".tmesh"
UNDO_HISTORY_LIMIT     = 10

# --- UI theme colors ---
# Mid-dark grey background (Alien/80s sci-fi neon aesthetic)
COLOR_BG_DARK      = "#1e1e2e"
COLOR_BG_MID       = "#2a2a3e"
COLOR_BG_PANEL     = "#25253a"
COLOR_ACCENT_CYAN  = "#00f5ff"
COLOR_ACCENT_AMBER = "#ffb300"
COLOR_ACCENT_GREEN = "#39ff14"
COLOR_TEXT_PRIMARY = "#e0e0f0"
COLOR_TEXT_DIM     = "#7a7a9a"
COLOR_HIGHLIGHT    = "#3a3a5c"

# --- Element quality color scale (green → red, standard FEA) ---
QUALITY_COLOR_GOOD = (0.0, 1.0, 0.0)   # RGB green
QUALITY_COLOR_MID  = (1.0, 1.0, 0.0)   # RGB yellow
QUALITY_COLOR_BAD  = (1.0, 0.0, 0.0)   # RGB red

# --- CFD quality metric limits ---
NON_ORTHOGONALITY_IDEAL  = 40.0   # degrees — OpenFOAM ideal
NON_ORTHOGONALITY_LIMIT  = 70.0   # degrees — OpenFOAM hard limit

# --- y+ calculator ---
# Flat-plate turbulent: Cf = 0.026 * Re^(-1/7)
CF_COEFFICIENT = 0.026
CF_EXPONENT    = -1.0 / 7.0
