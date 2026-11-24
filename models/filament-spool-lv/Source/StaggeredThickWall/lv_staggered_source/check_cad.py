"""Run current revision CAD checks; never slicing."""
import runpy
from pathlib import Path
R=Path(__file__).resolve().parent
for name in ("check_assembly.py","check_clocking.py","check_lock_pose.py","check_export.py"):
 runpy.run_path(str(R/name),run_name="__main__")
