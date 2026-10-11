SET SESSION iceberg.compression_codec='ZSTD';
CREATE TABLE iceberg.bronze_orc_zstd.customer WITH (format='ORC') AS SELECT custkey, mktsegment FROM tpch.sf1.customer;
