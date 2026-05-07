-- Remove collection_id column from br_bookmarks (collections feature removed)
ALTER TABLE br_bookmarks DROP COLUMN IF EXISTS collection_id;

-- Drop br_collections table
DROP TABLE IF EXISTS br_collections;
