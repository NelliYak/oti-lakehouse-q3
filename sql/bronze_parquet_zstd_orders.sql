SET SESSION iceberg.compression_codec='ZSTD';
CREATE TABLE iceberg.bronze.orders WITH (format='PARQUET') AS SELECT orderkey, custkey, orderdate, shippriority FROM tpch.sf1.orders;
