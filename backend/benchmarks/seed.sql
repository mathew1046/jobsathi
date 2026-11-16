-- Deterministic synthetic catalog, not real vacancies. Never run in a production database.
-- Independent hash-derived city/role/status distributions avoid correlation with recency.
INSERT INTO jobs (identity_key, title, company, location, city_key, country_code,
                  source, url, description, salary, is_active, posted_at, updated_at)
SELECT md5('benchmark-' || i), role, 'Synthetic employer ' || i, city, lower(city),
       CASE WHEN mod(i, 23) = 0 THEN 'US' ELSE 'IN' END,
       'Synthetic benchmark', 'https://example.invalid/jobs/' || i,
       role || '. ' || repeat(
           'Work with an experienced team. Training and equipment provided. '
           'Day and evening shifts available. Follow procedures, maintain records, '
           'and communicate clearly with colleagues. ', 3),
       '18000-30000/month', mod(i, 10) <> 0,
       timestamptz '2026-11-01 00:00:00+00' - mod(i * 1009, 525600) * interval '1 minute',
       timestamptz '2026-11-01 00:00:00+00'
FROM (
    SELECT i,
       (ARRAY['Delivery Driver','Electrician','Plumber','Warehouse Helper','Security Guard',
              'Factory Worker','AC Technician','Construction Worker','Truck Driver',
              'Mechanic','Forklift Operator','Housekeeping Staff'])[
           1 + mod(hashtextextended('role-' || i, 42) & 2147483647, 12)::integer] AS role,
       (ARRAY['Bengaluru','Delhi','Mumbai','Chennai','Hyderabad','Pune','Kolkata','Ahmedabad',
              'Jaipur','Lucknow','Kochi','Indore','Surat','Nagpur','Bhopal','Patna',
              'Coimbatore','Chandigarh','Visakhapatnam','Thiruvananthapuram'])[
           1 + mod(hashtextextended('city-' || i, 42) & 2147483647, 20)::integer] AS city
    FROM generate_series(1, %(rows)s) AS i
) AS generated;
