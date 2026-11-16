from pathlib import Path
import re,collections,json
root=Path(__file__).resolve().parent;reports=[]
for p in sorted(root.glob('*.stl')):
 lines=re.findall(r'vertex\s+([-+\deE.]+)\s+([-+\deE.]+)\s+([-+\deE.]+)',p.read_text());v=[tuple(float(c) for c in a) for a in lines];assert len(v)%3==0
 edges=collections.Counter();orient=collections.Counter();volume=0
 for i in range(0,len(v),3):
  a,b,c=v[i:i+3];volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
  for u,w in [(a,b),(b,c),(c,a)]:
   edge=tuple(sorted((u,w)));edges[edge]+=1;orient[edge]+=1 if u<w else -1
 bad=sum(v!=2 for v in edges.values());flips=sum(v!=0 for v in orient.values())
 r={'file':p.name,'triangles':len(v)//3,'edge_count':len(edges),'nonmanifold_or_open_edges':bad,'inconsistently_oriented_edges':flips,'signed_volume_mm3':volume};reports.append(r);print(r)
 assert bad==0 and flips==0 and volume>0
(root/'stl_validation.json').write_text(json.dumps(reports,indent=2))
