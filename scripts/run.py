"""Build medallion, benchmark four encodings, validate and demonstrate snapshots."""
import csv, json, statistics, time
from pathlib import Path
from trino_client import query
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'results'; SQL=ROOT/'sql'
OUT.mkdir(exist_ok=True); SQL.mkdir(exist_ok=True)
log=[]
def execute(sql,codec=None):
    print(sql[:110].replace('\n',' '),flush=True)
    r=query(sql,codec); log.append({'sql':sql,'session_compression_codec':codec,**r})
    (OUT/'query_log.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
    return r
def save(name,sql):
    (SQL/name).write_text(sql+';\n',encoding='utf-8')
def same_result(actual,reference):
    return len(actual)==len(reference) and all(a[0]==b[0] and a[2:]==b[2:]
        and abs(float(a[1])-float(b[1]))<.00001 for a,b in zip(actual,reference))
def q3(prefix):
    return f'''SELECT l.orderkey, SUM(l.extendedprice * (1 - l.discount)) AS revenue,
o.orderdate, o.shippriority
FROM {prefix}.customer c JOIN {prefix}.orders o ON c.custkey=o.custkey
JOIN {prefix}.lineitem l ON l.orderkey=o.orderkey
WHERE c.mktsegment='BUILDING' AND o.orderdate < DATE '1995-03-15'
AND l.shipdate > DATE '1995-03-15'
GROUP BY l.orderkey,o.orderdate,o.shippriority ORDER BY revenue DESC LIMIT 10'''
cols={'customer':'custkey, mktsegment','orders':'orderkey, custkey, orderdate, shippriority',
      'lineitem':'orderkey, linenumber, extendedprice, discount, shipdate'}
for _ in range(120):
    try: query('SELECT 1'); break
    except Exception: time.sleep(2)
for schema in ['bronze','bronze_parquet_gzip','bronze_orc_gzip','bronze_orc_zstd','silver','gold']:
    execute(f'CREATE SCHEMA IF NOT EXISTS iceberg.{schema}')
build=[]; sizes=[]; cases=[('PARQUET','ZSTD','bronze'),('PARQUET','GZIP','bronze_parquet_gzip'),
    ('ORC','GZIP','bronze_orc_gzip'),('ORC','ZSTD','bronze_orc_zstd')]
for fmt,codec,schema in cases:
    total=0
    for table,columns in cols.items():
        execute(f'DROP TABLE IF EXISTS iceberg.{schema}.{table}')
        sql=f"CREATE TABLE iceberg.{schema}.{table} WITH (format='{fmt}') AS SELECT {columns} FROM tpch.sf1.{table}"
        save(f'bronze_{fmt.lower()}_{codec.lower()}_{table}.sql',f"SET SESSION iceberg.compression_codec='{codec}';\n"+sql)
        r=execute(sql,codec); total+=r['wall_seconds']
        rows=execute(f'SELECT count(*) FROM iceberg.{schema}.{table}')['rows'][0][0]
        size=execute(f'SELECT sum(file_size_in_bytes), count(*) FROM iceberg.{schema}."{table}$files"')['rows'][0]
        sizes.append({'schema':schema,'table':table,'format':fmt,'codec':codec,'rows':rows,'bytes':size[0],'files':size[1], 'write_seconds':r['wall_seconds']})
    build.append({'format':fmt,'codec':codec,'schema':schema,'write_seconds':total,
        'bytes':sum(s['bytes'] for s in sizes if s['schema']==schema)})
reference=execute(q3('tpch.sf1'))['rows']; save('reference_q3.sql',q3('tpch.sf1'))
checks={}; checks['bronze_counts']={s['table']:s['rows'] for s in sizes if s['schema']=='bronze'}
quality={
 'customer_invalid':"SELECT count(*) FROM iceberg.bronze.customer WHERE custkey IS NULL OR mktsegment IS NULL OR trim(mktsegment)=''",
 'orders_invalid':"SELECT count(*) FROM iceberg.bronze.orders WHERE orderkey IS NULL OR custkey IS NULL OR orderdate IS NULL OR shippriority IS NULL",
 'lineitem_invalid':"SELECT count(*) FROM iceberg.bronze.lineitem WHERE orderkey IS NULL OR linenumber IS NULL OR shipdate IS NULL OR extendedprice IS NULL OR extendedprice<0 OR discount IS NULL OR discount<0 OR discount>1",
 'customer_duplicates':"SELECT count(*) FROM (SELECT custkey FROM iceberg.bronze.customer GROUP BY custkey HAVING count(*)>1)",
 'orders_duplicates':"SELECT count(*) FROM (SELECT orderkey FROM iceberg.bronze.orders GROUP BY orderkey HAVING count(*)>1)",
 'lineitem_duplicates':"SELECT count(*) FROM (SELECT orderkey,linenumber FROM iceberg.bronze.lineitem GROUP BY orderkey,linenumber HAVING count(*)>1)",
 'orphan_orders':"SELECT count(*) FROM iceberg.bronze.orders o LEFT JOIN iceberg.bronze.customer c ON o.custkey=c.custkey WHERE c.custkey IS NULL",
 'orphan_lines':"SELECT count(*) FROM iceberg.bronze.lineitem l LEFT JOIN iceberg.bronze.orders o ON l.orderkey=o.orderkey WHERE o.orderkey IS NULL"}
for name,sql in quality.items():
    save(name+'.sql',sql); checks[name]=execute(sql)['rows'][0][0]; assert checks[name]==0,(name,checks[name])
silver="""CREATE TABLE iceberg.silver.order_lines WITH (format='PARQUET') AS
SELECT l.orderkey,l.linenumber,o.custkey,upper(trim(c.mktsegment)) AS mktsegment,
o.orderdate,l.shipdate,o.shippriority,
CAST(l.extendedprice AS DECIMAL(18,2)) AS extendedprice,
CAST(l.discount AS DECIMAL(4,2)) AS discount,
CAST(CAST(l.extendedprice AS DECIMAL(18,2)) * (DECIMAL '1.00' - CAST(l.discount AS DECIMAL(4,2))) AS DECIMAL(20,4)) AS line_revenue
FROM iceberg.bronze.customer c JOIN iceberg.bronze.orders o ON c.custkey=o.custkey
JOIN iceberg.bronze.lineitem l ON o.orderkey=l.orderkey
WHERE upper(trim(c.mktsegment))='BUILDING' AND o.orderdate<DATE '1995-03-15'
AND l.shipdate>DATE '1995-03-15' AND l.extendedprice>=0 AND l.discount BETWEEN 0 AND 1"""
gold="""CREATE TABLE iceberg.gold.shipping_priority WITH (format='PARQUET') AS
SELECT orderkey,sum(line_revenue) AS revenue,orderdate,shippriority
FROM iceberg.silver.order_lines GROUP BY orderkey,orderdate,shippriority
ORDER BY revenue DESC LIMIT 10"""
for table,sql,name in [('silver.order_lines',silver,'silver.sql'),('gold.shipping_priority',gold,'gold.sql')]:
    execute('DROP TABLE IF EXISTS iceberg.'+table); save(name,"SET SESSION iceberg.compression_codec='ZSTD';\n"+sql); execute(sql,'ZSTD')
actual=execute('SELECT * FROM iceberg.gold.shipping_priority ORDER BY revenue DESC')['rows']
assert [r[0] for r in actual]==[r[0] for r in reference]
assert all(abs(float(a[1])-float(b[1]))<.00001 and a[2:]==b[2:] for a,b in zip(actual,reference))
checks['gold_matches_reference']=True
(OUT/'gold.json').write_text(json.dumps(actual,indent=2),encoding='utf-8')
for table in ['silver.order_lines','gold.shipping_priority']:
    schema,name=table.split('.'); n=execute('SELECT count(*) FROM iceberg.'+table)['rows'][0][0]
    b,f=execute(f'SELECT sum(file_size_in_bytes),count(*) FROM iceberg.{schema}."{name}$files"')['rows'][0]
    sizes.append({'schema':schema,'table':name,'format':'PARQUET','codec':'ZSTD','rows':n,'bytes':b,'files':f,'write_seconds':None})
for case in build:
    sql=q3('iceberg.'+case['schema']); save('q3_'+case['schema']+'.sql',sql)
    assert same_result(execute(sql)['rows'],reference)
    case['runs']=[]
# Interleave measured runs to reduce systematic bias from run order / JVM warm-up.
for round_no in range(5):
    order=build[round_no%4:]+build[:round_no%4]
    for case in order:
        r=execute(q3('iceberg.'+case['schema'])); assert same_result(r['rows'],reference)
        case['runs'].append({'round':round_no+1,'wall_seconds':r['wall_seconds'],
            'query_id':r['query_id'],'elapsed_ms':r['stats'].get('elapsedTimeMillis'),
            'processed_bytes':r['stats'].get('processedBytes')})
for case in build:
    case['median_seconds']=statistics.median(r['wall_seconds'] for r in case['runs'])
    case['min_seconds']=min(r['wall_seconds'] for r in case['runs'])
    case['max_seconds']=max(r['wall_seconds'] for r in case['runs'])
(OUT/'benchmark.json').write_text(json.dumps(build,indent=2),encoding='utf-8')
with (OUT/'benchmark.csv').open('w',newline='',encoding='utf-8-sig') as f:
    writer=csv.DictWriter(f,fieldnames=['format','codec','bytes','write_seconds','median_seconds','min_seconds','max_seconds'])
    writer.writeheader(); writer.writerows({k:v for k,v in c.items() if k in writer.fieldnames} for c in build)
(OUT/'table_sizes.json').write_text(json.dumps(sizes,indent=2),encoding='utf-8')
evolution=["ALTER TABLE iceberg.silver.order_lines ADD COLUMN source_system VARCHAR",
    "ALTER TABLE iceberg.silver.order_lines RENAME COLUMN source_system TO data_source"]
for sql in evolution: execute(sql)
checks['schema_evolution_nulls']=execute('SELECT count(*),count(data_source) FROM iceberg.silver.order_lines')['rows']
snap=execute('SELECT snapshot_id FROM iceberg.silver."order_lines$snapshots" ORDER BY committed_at DESC LIMIT 1')['rows'][0][0]
before=execute('SELECT count(*) FROM iceberg.silver.order_lines')['rows'][0][0]
delete='DELETE FROM iceberg.silver.order_lines WHERE orderkey=(SELECT min(orderkey) FROM iceberg.silver.order_lines)'
execute(delete); after=execute('SELECT count(*) FROM iceberg.silver.order_lines')['rows'][0][0]
historic=execute(f'SELECT count(*) FROM iceberg.silver.order_lines FOR VERSION AS OF {snap}')['rows'][0][0]
rollback=f"CALL iceberg.system.rollback_to_snapshot('silver','order_lines',{snap})"
execute(rollback); restored=execute('SELECT count(*) FROM iceberg.silver.order_lines')['rows'][0][0]
assert before==historic==restored and after<before
checks['time_travel']={'snapshot_id':snap,'before':before,'after_delete':after,'historic':historic,'restored':restored}
save('schema_evolution.sql',';\n'.join(evolution))
save('time_travel.sql',f'-- Snapshot id is specific to this execution. Read a fresh id from $snapshots.\n{delete};\nSELECT count(*) FROM iceberg.silver.order_lines FOR VERSION AS OF {snap};\n{rollback}')
(OUT/'checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('ALL CHECKS PASSED',flush=True)
