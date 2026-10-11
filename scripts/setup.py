"""Initialize the local catalog. Uses Python standard library only."""
import json, subprocess, time, urllib.request, urllib.error
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def api(path, payload=None):
    req = urllib.request.Request('http://localhost:8181'+path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b'{}')
for _ in range(120):
    try:
        api('/health'); break
    except Exception: time.sleep(2)
else: raise RuntimeError('Lakekeeper did not start')
try:
    api('/management/v1/bootstrap', {'accept-terms-of-use':True})
except urllib.error.HTTPError as e:
    if e.code not in (400,409): raise
subprocess.run(['docker','compose','exec','-T','minio','mc','alias','set','local',
    'http://localhost:9000','student','student-local-password'],cwd=ROOT,check=True)
subprocess.run(['docker','compose','exec','-T','minio','mc','mb','--ignore-existing',
    'local/lakehouse'],cwd=ROOT,check=True)
warehouses = api('/management/v1/warehouse?project-id=00000000-0000-0000-0000-000000000000')
if not any(w.get('name',w.get('warehouse-name'))=='practice' for w in warehouses.get('warehouses',[])):
    api('/management/v1/warehouse', {
        'warehouse-name':'practice','project-id':'00000000-0000-0000-0000-000000000000',
        'storage-profile':{'type':'s3','bucket':'lakehouse','key-prefix':'practice',
            'endpoint':'http://minio:9000','region':'us-east-1','path-style-access':True,
            'flavor':'s3-compat','sts-enabled':False},
        'storage-credential':{'type':'s3','credential-type':'access-key',
            'access-key-id':'student','secret-access-key':'student-local-password'}})
print('Warehouse practice ready')
