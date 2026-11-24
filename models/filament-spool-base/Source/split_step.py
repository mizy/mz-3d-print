"""Export two existing spool solids to separate native STEP files; no slicing.
Usage: python split_step.py INPUT.step [--output DIR]
Input is preserved. Existing output files are never overwritten.
"""
import argparse,json
from pathlib import Path
import cadquery as cq

def split(path,output=None):
    path=Path(path);out=Path(output) if output else path.parent
    shape=cq.importers.importStep(str(path)).val()
    solids=sorted(shape.Solids(),key=lambda s:s.BoundingBox().zlen,reverse=True)
    if len(solids)!=2 or not shape.isValid(): raise ValueError('Expected two valid spool solids')
    if abs(solids[0].BoundingBox().zlen-solids[1].BoundingBox().zlen)<0.01: raise ValueError('Cannot distinguish wide/narrow by height')
    targets=[out/(path.stem+'_'+label+'.step') for label in ('wide','narrow')]
    if any(p.exists() for p in targets): raise FileExistsError('Output exists; select a new directory')
    out.mkdir(parents=True,exist_ok=True);report=[]
    for label,s,target in zip(('wide','narrow'),solids,targets):
        cq.exporters.export(s,str(target),exportType='STEP',opt={'write_pcurves':False})
        back=cq.importers.importStep(str(target)).val()
        assert back.isValid() and len(back.Solids())==1
        vd=abs(s.Volume()-back.Volume());ad=abs(s.Area()-back.Area())
        a,b=s.BoundingBox(),back.BoundingBox()
        bd=max(abs(getattr(a,k)-getattr(b,k)) for k in ('xmin','xmax','ymin','ymax','zmin','zmax'))
        assert vd/max(s.Volume(),1)<1e-6 and ad<0.001 and bd<1e-5
        report.append({'part':label,'path':str(target),'solids':1,'valid':True,'volume_difference_mm3':vd,'area_difference_mm2':ad,'bbox_max_difference_mm':bd})
    print(json.dumps(report,indent=2));return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();split(a.input,a.output)
