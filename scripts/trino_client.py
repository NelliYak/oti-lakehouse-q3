"""Small synchronous Trino REST client; no pip packages required."""
import json, time, urllib.request
def query(sql, codec=None):
    started=time.perf_counter()
    headers={'X-Trino-User':'student','Content-Type':'text/plain; charset=utf-8'}
    if codec: headers['X-Trino-Session']='iceberg.compression_codec='+codec
    req=urllib.request.Request('http://localhost:8080/v1/statement',data=sql.encode(),headers=headers)
    rows=[]; columns=[]; stats={}; query_id=None
    while True:
        with urllib.request.urlopen(req,timeout=120) as r: result=json.load(r)
        query_id=result.get('id',query_id)
        if 'error' in result: raise RuntimeError(json.dumps(result['error'],ensure_ascii=False))
        columns=result.get('columns',columns); rows.extend(result.get('data',[]))
        stats=result.get('stats',stats)
        if 'nextUri' not in result: break
        req=urllib.request.Request(result['nextUri'],headers={'X-Trino-User':'student'})
        time.sleep(.05)
    return {'columns':[c['name'] for c in columns],'rows':rows,'stats':stats,
            'query_id':query_id,'wall_seconds':time.perf_counter()-started}
if __name__=='__main__':
    import sys
    print(json.dumps(query(' '.join(sys.argv[1:])),ensure_ascii=False,indent=2))
