exec(open('/tmp/chanel_official_native/assembly_check.py').read().split('for h,a in')[0])
import numpy as np
poses=[(float(h),51.) for h in np.arange(72.,66.39,-.2)]+[(66.4,float(a)) for a in list(range(51,8,-2))+[8]]+[(66.5,8.),(66.4,0.)]
for h,a in poses:
 c=w.intersect(place(h,a));row={'H':h,'angle':a,'valid':c.isValid(),'volume':sum(s.Volume() for s in c.Solids())};rows.append(row)
print('PATH max before pull/detent',max(r['volume'] for r in rows[:-2]),'last checks',rows[-2:],flush=True);(D/'assembly_path.json').write_text(json.dumps({'path':rows,'limitations':['Discrete static poses only.','8deg is a no-interference pre-detent retained region, not proven final locked position.','0deg and passing detent involve official-source rigid overlap; no elastic simulation or physical fit validation.']},indent=2))
