SET SESSION iceberg.compression_codec='GZIP';
CREATE TABLE iceberg.bronze_orc_gzip.customer WITH (format='ORC') AS SELECT custkey, mktsegment FROM tpch.sf1.customer;
