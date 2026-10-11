SELECT count(*) FROM iceberg.bronze.orders WHERE orderkey IS NULL OR custkey IS NULL OR orderdate IS NULL OR shippriority IS NULL;
