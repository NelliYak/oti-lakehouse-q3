SET SESSION iceberg.compression_codec='ZSTD';
CREATE TABLE iceberg.silver.order_lines WITH (format='PARQUET') AS
SELECT l.orderkey,l.linenumber,o.custkey,upper(trim(c.mktsegment)) AS mktsegment,
o.orderdate,l.shipdate,o.shippriority,
CAST(l.extendedprice AS DECIMAL(18,2)) AS extendedprice,
CAST(l.discount AS DECIMAL(4,2)) AS discount,
CAST(CAST(l.extendedprice AS DECIMAL(18,2)) * (DECIMAL '1.00' - CAST(l.discount AS DECIMAL(4,2))) AS DECIMAL(20,4)) AS line_revenue
FROM iceberg.bronze.customer c JOIN iceberg.bronze.orders o ON c.custkey=o.custkey
JOIN iceberg.bronze.lineitem l ON o.orderkey=l.orderkey
WHERE upper(trim(c.mktsegment))='BUILDING' AND o.orderdate<DATE '1995-03-15'
AND l.shipdate>DATE '1995-03-15' AND l.extendedprice>=0 AND l.discount BETWEEN 0 AND 1;
