import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))                      # import core
sys.path.insert(0, str(ROOT / "streamlit_app"))    # import ui (used by the pages)
