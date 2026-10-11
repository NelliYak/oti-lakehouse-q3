SET SESSION iceberg.compression_codec='ZSTD';
CREATE TABLE iceberg.bronze_orc_zstd.lineitem WITH (format='ORC') AS SELECT orderkey, linenumber, extendedprice, discount, shipdate FROM tpch.sf1.lineitem;
