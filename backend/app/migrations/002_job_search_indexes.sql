-- Apply only after capturing the integrity-index-only baseline.
-- Equality filters lead; recency/id match both ORDER BY and the keyset cursor.
-- Inactive listings need no entries in the public search indexes.
CREATE INDEX jobs_active_city_recent_idx
    ON jobs (country_code, city_key, posted_at DESC, id DESC)
    WHERE is_active;

-- The city-prefixed index cannot provide country-wide recency ordering.
CREATE INDEX jobs_active_country_recent_idx
    ON jobs (country_code, posted_at DESC, id DESC)
    WHERE is_active;

-- Supports rare terms and no-match searches where recency scans would visit many rows.
CREATE INDEX jobs_active_search_document_idx
    ON jobs USING gin (search_document)
    WHERE is_active;

ANALYZE jobs;
