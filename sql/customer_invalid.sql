SELECT count(*) FROM iceberg.bronze.customer WHERE custkey IS NULL OR mktsegment IS NULL OR trim(mktsegment)='';
