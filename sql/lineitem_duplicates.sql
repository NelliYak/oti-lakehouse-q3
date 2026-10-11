SELECT count(*) FROM (SELECT orderkey,linenumber FROM iceberg.bronze.lineitem GROUP BY orderkey,linenumber HAVING count(*)>1);
