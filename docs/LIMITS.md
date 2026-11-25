# Current limits and unverified deliverables

This list separates implemented local behavior from features, inputs, and acceptance evidence that are not available. Check [`TEST_REPORT.md`](TEST_REPORT.md) for dated results and verify the exact SHA before treating any check as current.

- **AI is off.** There is no trained model, ONNX export, inference worker, measured evaluation, or category suggestion in the reviewer UI. No model or accuracy claims are made.
- **Geography is synthetic.** The seeded Hyderabad ward is a demo polygon, not an authoritative municipal ward boundary or pilot area. The owner must provide source-backed pilot geometry and coordinates.
- **Evidence photos on Render free are ephemeral.** Uploaded evidence can disappear when the web service sleeps, restarts, or redeploys. Use only synthetic demo records and original illustration photos there; do not enter real complaints or personal photos.
- **The Render free host does not run the application scheduler.** Reminders, notification delivery, SLA jobs, and scheduled `purge_expired` are not run on that host. A durable deployment needs a separately scheduled process or managed job.
- **Email is console-only in local development.** The free Render demo does not provide the configured SMTP path; production email delivery needs a separately configured provider and owner-supplied credentials.
- **No live demo URL is confirmed.** The Render + Neon browser instructions are in [`DEPLOY_FREE.md`](DEPLOY_FREE.md), but a running Render service, Neon PostGIS permission, public HTTPS URL, and end-to-end deployment are not verified here.
- **Exact-head CI is not assumed.** A CI result applies only to the SHA named in the run. Historical green runs do not verify later commits; current status is pending owner-refreshed `_ci` evidence.
- **Production security and operations remain incomplete.** No deployed-edge scan, scheduled off-host backup, production restore, uptime/error monitor, or live device acceptance is evidenced.
- **No official municipal integration exists.** GPS pins and photos can be incomplete or inaccurate; the system is not an emergency service.
- **Map tiles are demo-only.** OpenStreetMap tiles are used with attribution. Reassess the tile provider and terms before scaling traffic.
