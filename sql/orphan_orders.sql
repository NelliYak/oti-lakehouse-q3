SELECT count(*) FROM iceberg.bronze.orders o LEFT JOIN iceberg.bronze.customer c ON o.custkey=c.custkey WHERE c.custkey IS NULL;
