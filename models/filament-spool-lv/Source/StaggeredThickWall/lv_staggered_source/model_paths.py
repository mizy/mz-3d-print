"""Resolve package and linked Mac project layouts without changing shared files."""
import os
from pathlib import Path
SOURCE_DIR=Path(__file__).resolve().parent
mac_project=SOURCE_DIR.parents[2]/'Models'/'StaggeredThickWall'
MODELS_DIR=Path(os.environ['LV_MODELS_DIR']) if os.environ.get('LV_MODELS_DIR') else (mac_project if SOURCE_DIR.name=='lv_staggered_source' and mac_project.is_dir() else SOURCE_DIR.parent/'Models')
