# Deferred work and external gates

This file records work that cannot be completed safely from the current local repository alone. Items stay deferred until their stated input or acceptance evidence exists.

| Item | Why it remains open | Unblock condition |
| --- | --- | --- |
| Public HTTPS deployment | No domain, server/PaaS account, or owner-controlled deployment credentials are configured. | Owner supplies the target and access; deploy from a reviewed commit and verify public HTTPS. |
| Authoritative pilot ward | The local Hyderabad square is synthetic demo geography, not a real ward polygon. | Owner supplies the pilot center and an authoritative ward boundary source with effective dates. |
| AI classifier and measured metrics | `ml/data/<category>/` has no owner images or grouping manifest; candidate public data rights/domain fit are unresolved. | Supply rights-cleared product photos and group/source metadata, or approve a verified public dataset; then evaluate on a group-held-out test split. |
| Remote CI evidence | No Git remote is configured, so GitHub Actions cannot run against this workspace commit. | Configure the owner-controlled repository remote and push the reviewed commit; record the CI result. |
| Production backups, monitoring, and restore | Only a local disposable restore has been rehearsed. There is no production host or owner-approved monitoring account. | Deploy to an owner-controlled environment, configure restricted off-host backups and monitoring, and rehearse a production restore. |
| Device and pilot acceptance | No two physical phones, full desktop assistive-technology pass, or pilot trial are available to this local run. | Owner/operator tests the report and triage workflow on the required devices and records results. |
| Showcase CSP/SRI cleanup | The supplied static reference screens use inline code and third-party assets. A strict policy may break the references until assets are bundled and reviewed. | Bundle and audit those resources, then set a tested policy before public release. |
| Orphaned local media reconciliation | The development media volume contains six files without current `Evidence` rows; ownership and retention are unknown. | Owner identifies ownership and approves a retention/deletion action. Do not delete them based only on missing database references. |

The duplicate-candidate feature is no longer deferred; its implementation and local tests are tracked in the current progress and test report.

Features explicitly outside the frozen v1 scope (mobile app/PWA, public dashboard/map, messaging integrations, autonomous AI decisions, and municipal system integrations) are not pending v1 work.
