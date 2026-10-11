SET SESSION iceberg.compression_codec='ZSTD';
CREATE TABLE iceberg.bronze_orc_zstd.orders WITH (format='ORC') AS SELECT orderkey, custkey, orderdate, shippriority FROM tpch.sf1.orders;
