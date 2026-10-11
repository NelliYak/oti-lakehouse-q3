SET SESSION iceberg.compression_codec='GZIP';
CREATE TABLE iceberg.bronze_orc_gzip.orders WITH (format='ORC') AS SELECT orderkey, custkey, orderdate, shippriority FROM tpch.sf1.orders;
