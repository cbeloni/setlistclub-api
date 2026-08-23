ALTER TABLE chord_sheets
ADD COLUMN is_bucket_storage BOOLEAN NOT NULL DEFAULT FALSE AFTER image_data;
