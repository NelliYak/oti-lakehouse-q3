SELECT count(*) FROM (SELECT custkey FROM iceberg.bronze.customer GROUP BY custkey HAVING count(*)>1);
