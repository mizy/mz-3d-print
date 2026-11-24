"""Check shared links/defaults without slicing or modifying any model."""
from pathlib import Path
import ast, json, subprocess, sys
R = Path(__file__).resolve().parents[3]
BASE = R / 'models/filament-spool-base'
manifest = json.loads((BASE/'Notes/shared-source-migration.json').read_text())
for name in manifest['compatibility_links']:
    p = R/name
    assert p.is_symlink() and p.is_file(), name
    assert p.resolve().parent == BASE/'Source', name
for name in ('filament-spool-chanel/Source/chanel_reinforced_connected_fix',
             'filament-spool-lv/Source/StaggeredThickWall/lv_staggered_source'):
    source = R/'models'/name
    for p in source.glob('*.py'):
        ast.parse(p.read_text())
    # Separate interpreter avoids flat-module import collisions between brands.
    code = '''import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import build_light as B, build_official as O, official_hub as H
assert B.R == Path(sys.argv[1]).resolve()
assert Path(H.__file__).resolve().parent == Path(sys.argv[2]).resolve()
q=json.loads((B.R/'light_parameters.json').read_text())
O.load(B.R/q['baseline_parameters'])
print('PASS',sys.argv[1])
'''
    subprocess.run([sys.executable,'-c',code,str(source),str(BASE/'Source')],check=True)
print('PASS shared links:',len(manifest['compatibility_links']))
