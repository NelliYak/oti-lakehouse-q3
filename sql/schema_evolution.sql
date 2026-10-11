ALTER TABLE iceberg.silver.order_lines ADD COLUMN source_system VARCHAR;
ALTER TABLE iceberg.silver.order_lines RENAME COLUMN source_system TO data_source;
