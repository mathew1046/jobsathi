# JobSathi PostgreSQL search measurements

Generated: 2026-11-16T08:35:50.370644+00:00

| Query | Path | Before median / p95 (ms) | After median / p95 (ms) | Median speedup |
|---|---|---:|---:|---:|
| frontend_driver_bengaluru | sql | 53.202 / 63.149 | 1.026 / 1.144 | 51.87× |
| frontend_driver_bengaluru | http | 55.965 / 64.462 | 3.329 / 3.702 | 16.81× |
| driver_bengaluru | sql | 53.172 / 63.105 | 0.985 / 1.240 | 54.00× |
| driver_bengaluru | http | 55.454 / 64.921 | 3.163 / 3.496 | 17.53× |
| plumber_pune | sql | 55.659 / 78.436 | 1.275 / 1.468 | 43.67× |
| plumber_pune | http | 57.819 / 75.415 | 3.305 / 3.560 | 17.49× |
| electrician_india | sql | 53.787 / 60.877 | 1.282 / 1.468 | 41.94× |
| electrician_india | http | 56.806 / 64.680 | 3.408 / 3.760 | 16.67× |

All dataset fingerprints, query SQL/parameters, returned-page hashes, PostgreSQL settings,
sample counts and cache policies matched. Raw individual samples and hardware metadata are in before.json / after.json.
p95 uses the nearest-rank definition. HTTP is real loopback TCP to Uvicorn, including routing, pooling,
query execution, scoring, serialization, response transfer and client JSON decoding.
