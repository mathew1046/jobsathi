-- Baseline: integrity indexes only. Search indexes are a separate migration.
CREATE TABLE sessions (
    id uuid PRIMARY KEY,
    responses jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(responses) = 'array'),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    profile jsonb,
    pdf_filename text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE jobs (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    identity_key text NOT NULL UNIQUE,
    title text NOT NULL CHECK (length(btrim(title)) > 0),
    company text NOT NULL,
    location text NOT NULL,
    city_key text NOT NULL,
    country_code text NOT NULL DEFAULT 'IN' CHECK (country_code ~ '^[A-Z]{2}$'),
    source text NOT NULL,
    url text NOT NULL,
    description text NOT NULL DEFAULT '',
    salary text NOT NULL DEFAULT 'Not specified',
    is_active boolean NOT NULL DEFAULT true,
    posted_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    search_document tsvector GENERATED ALWAYS AS (
        to_tsvector('simple', title || ' ' || description)
    ) STORED
);
