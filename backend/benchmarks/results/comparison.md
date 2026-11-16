# JobSathi PostgreSQL search measurements

Generated: 2026-11-16T08:09:35.050182+00:00

| Query | Path | Before median / p95 (ms) | After median / p95 (ms) | Median speedup |
|---|---|---:|---:|---:|
| driver_bengaluru | sql | 52.886 / 71.924 | 0.950 / 1.579 | 55.64× |
| driver_bengaluru | http | 55.400 / 71.892 | 3.190 / 4.650 | 17.37× |
| plumber_pune | sql | 65.120 / 88.230 | 1.136 / 1.918 | 57.32× |
| plumber_pune | http | 68.246 / 83.104 | 3.405 / 5.034 | 20.04× |
| electrician_india | sql | 65.235 / 79.541 | 1.091 / 1.929 | 59.80× |
| electrician_india | http | 68.360 / 79.697 | 3.358 / 5.106 | 20.36× |

All dataset fingerprints, query SQL/parameters, returned-page hashes, PostgreSQL settings,
sample counts and cache policies matched. Raw individual samples and hardware metadata are in before.json / after.json.
p95 uses the nearest-rank definition. HTTP is real loopback TCP to Uvicorn, including routing, pooling,
query execution, scoring, serialization, response transfer and client JSON decoding.
