"""Read persisted Bronze through Trino JDBC, then aggregate in Spark."""
import json
from pyspark.sql import SparkSession, functions as F
spark=SparkSession.builder.appName('Bronze lakehouse demonstration').getOrCreate()
df=(spark.read.format('jdbc').option('url','jdbc:trino://trino:8080/iceberg/bronze')
    .option('driver','io.trino.jdbc.TrinoDriver').option('user','student')
    .option('dbtable','customer').load())
df.printSchema(); df.show(5,truncate=False)
result=df.groupBy('mktsegment').agg(F.count('*').alias('customers')).orderBy('mktsegment')
result.show(truncate=False)
rows=[r.asDict() for r in result.collect()]
assert sum(r['customers'] for r in rows)==150000
with open('/opt/results/spark_bronze.json','w') as f: json.dump(rows,f,indent=2)
spark.stop()
