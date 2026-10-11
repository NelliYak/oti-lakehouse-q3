SELECT count(*) FROM (SELECT orderkey FROM iceberg.bronze.orders GROUP BY orderkey HAVING count(*)>1);
