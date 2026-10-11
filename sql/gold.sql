SET SESSION iceberg.compression_codec='ZSTD';
CREATE TABLE iceberg.gold.shipping_priority WITH (format='PARQUET') AS
SELECT orderkey,sum(line_revenue) AS revenue,orderdate,shippriority
FROM iceberg.silver.order_lines GROUP BY orderkey,orderdate,shippriority
ORDER BY revenue DESC LIMIT 10;
