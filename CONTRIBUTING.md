# Contributing

Keep changes small and focused. Do not commit `.env` files, credentials, user photos, backups, model weights, or local `_ci` evidence. Preserve complaint authorization, append-only status/audit history, and all existing tests.

Before opening a pull request, run `docker compose run --rm checks` when the Docker engine is available and summarize any check that could not run. Include the commit SHA for CI evidence and do not describe a commit as verified unless the Actions run succeeded on that exact SHA.
