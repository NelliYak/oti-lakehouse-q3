-- Snapshot id belongs to this run; choose a fresh id before reproducing.
DELETE FROM iceberg.silver.order_lines WHERE orderkey=(SELECT min(orderkey) FROM iceberg.silver.order_lines);
SELECT count(*) FROM iceberg.silver.order_lines FOR VERSION AS OF 2653687598250934620;
CALL iceberg.system.rollback_to_snapshot('silver','order_lines',2653687598250934620);
