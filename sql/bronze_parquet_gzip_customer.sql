SET SESSION iceberg.compression_codec='GZIP';
CREATE TABLE iceberg.bronze_parquet_gzip.customer WITH (format='PARQUET') AS SELECT custkey, mktsegment FROM tpch.sf1.customer;
