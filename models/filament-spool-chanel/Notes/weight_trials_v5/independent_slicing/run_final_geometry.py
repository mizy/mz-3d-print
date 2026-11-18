from pathlib import Path
import time,subprocess,concurrent.futures,json
D=Path('/tmp/chanel_100g');S=Path('/tmp/chanel_weight_trials/original_lower_skin04');t=time.time()
while not (S/'validation.json').exists():
 if time.time()-t>300:raise TimeoutError('Final geometry validation not ready in300s')
 time.sleep(3)
print('validated source ready',flush=True)
def pack(part):
 tag='original_lower_skin04_'+part
 with open(D/(tag+'_pack.log'),'w') as f:subprocess.run(['/tmp/chanel-parametric-env/bin/python',str(D/'pack_brep.py'),str(S/(part+'_complete.brep')),tag],stdout=f,stderr=f,check=True)
 print('packed',part,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(pack,['wide','narrow']))
subprocess.run(['python3',str(D/'slice_candidate.py'),'original_lower_skin04_wide','original_lower_skin04_narrow'],check=True)
