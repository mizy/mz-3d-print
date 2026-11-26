"""Guard FreeCAD exporter inconsistencies: serialized coordinates must be mm."""
from pathlib import Path
import Part

def ensure_mm(file, expected):
    file=Path(file)
    actual=Part.read(str(file)).BoundBox
    target=expected.BoundBox
    length_keys=('XLength','YLength','ZLength')
    def match(scale):
        return all(abs(getattr(actual,k)-scale*getattr(target,k)) < .0001*scale for k in length_keys)
    if match(1000.):
        raw=file.read_bytes()
        old=b'LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT($,.METRE.)'
        new=b'LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.)'
        assert old in raw and new not in raw
        file.write_bytes(raw.replace(old,new))
        actual=Part.read(str(file)).BoundBox
    assert match(1.),(str(file),actual,target)
