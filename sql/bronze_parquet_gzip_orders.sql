SET SESSION iceberg.compression_codec='GZIP';
CREATE TABLE iceberg.bronze_parquet_gzip.orders WITH (format='PARQUET') AS SELECT orderkey, custkey, orderdate, shippriority FROM tpch.sf1.orders;
