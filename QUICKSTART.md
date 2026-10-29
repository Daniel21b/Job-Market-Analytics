# Explore the results

The primary frontend is a **Next.js / React / TypeScript dashboard**:

[Open Job Market Observatory](https://danielberhane.vercel.app/en/analytics)

Explore skill rankings, date/category filters, monthly distributions and aggregate exports. The data is a dated, verified snapshot with active and archived postings, not a feed of currently open jobs.

## Run the frontend locally

The frontend lives in the [Portfolio repository](https://github.com/Daniel21b/Portfolio), under `src/app/[locale]/analytics` and `src/components/analytics-dashboard`. Clone that repository, run `npm ci`, then `npm run dev` and open `/en/analytics`.

## Update the data

Run the pipeline and independently reconcile its files/database using `benchmarks/audit_frozen_output.py`, then measure the API. Export only aggregates:

```sh
python benchmarks/export_dashboard_snapshot.py \
  --evidence evidence/2026-10-29 \
  --output-dir /path/to/completed/pipeline-output \
  --destination /path/to/Portfolio/src/data/analytics-snapshot.json
```

The exporter requires a successful, audited run and checks totals. No descriptions or connection credentials are published. The frontend does not expose the processing API or connect directly to PostgreSQL.

## Legacy Streamlit URL

`app.py` now links to the new application; it no longer renders synthetic fallback results. The compatibility `Procfile` launches this notice. The previously documented `dashboard.py` was absent and is not a supported command. Historical Streamlit code remains in Git history.
