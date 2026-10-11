SET SESSION iceberg.compression_codec='ZSTD';
CREATE TABLE iceberg.bronze.customer WITH (format='PARQUET') AS SELECT custkey, mktsegment FROM tpch.sf1.customer;
