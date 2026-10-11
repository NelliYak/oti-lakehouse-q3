SET SESSION iceberg.compression_codec='GZIP';
CREATE TABLE iceberg.bronze_parquet_gzip.lineitem WITH (format='PARQUET') AS SELECT orderkey, linenumber, extendedprice, discount, shipdate FROM tpch.sf1.lineitem;
