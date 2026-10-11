SET SESSION iceberg.compression_codec='GZIP';
CREATE TABLE iceberg.bronze_orc_gzip.lineitem WITH (format='ORC') AS SELECT orderkey, linenumber, extendedprice, discount, shipdate FROM tpch.sf1.lineitem;
