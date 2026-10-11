SET SESSION iceberg.compression_codec='ZSTD';
CREATE TABLE iceberg.bronze.lineitem WITH (format='PARQUET') AS SELECT orderkey, linenumber, extendedprice, discount, shipdate FROM tpch.sf1.lineitem;
