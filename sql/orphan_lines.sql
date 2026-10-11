SELECT count(*) FROM iceberg.bronze.lineitem l LEFT JOIN iceberg.bronze.orders o ON l.orderkey=o.orderkey WHERE o.orderkey IS NULL;
