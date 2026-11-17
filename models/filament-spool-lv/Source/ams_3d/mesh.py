import sys,json
from pathlib import Path
pass
import gmsh,numpy as np
import os
CODE=Path(__file__).resolve().parent;R=Path(os.environ.get('AMS_OUTPUT',str(CODE/'work'))).resolve();R.mkdir(parents=True,exist_ok=True);h=float(sys.argv[1]);gmsh.initialize();gmsh.model.add('actual_wide_half')
gmsh.model.occ.importShapes(str(Path(os.environ.get('AMS_CAD',str(CODE.parent.parent/'Models/A_wide_PROTOTYPE.step')))));gmsh.model.occ.synchronize()
gmsh.option.setNumber('Mesh.MeshSizeMax',h);gmsh.option.setNumber('Mesh.MeshSizeMin',.5*h);gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',16);gmsh.option.setNumber('Mesh.Algorithm3D',1)
gmsh.model.mesh.generate(3)
tags,coords,_=gmsh.model.mesh.getNodes();p=coords.reshape(-1,3);lookup=np.zeros(int(max(tags))+1,dtype=int);lookup[tags]=np.arange(len(tags));types,ets,ens=gmsh.model.mesh.getElements(3);t=lookup[ens[types.index(4)]] if isinstance(types,list) else lookup[ens[list(types).index(4)]];t=t.reshape(-1,4)
np.savez_compressed(R/f'mesh_{h:g}.npz',p=p,t=t);print('RESULT',len(p),len(t),flush=True);gmsh.finalize()
