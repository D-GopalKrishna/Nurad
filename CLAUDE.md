## Plans

Plan files for this project live in `.vscode/plan/`, not `~/.claude/plans/`. When entering
plan mode for Nurad work, once a plan is approved, write (or split) the final plan into
`.vscode/plan/<NN>-<short-name>.md` and add a `## Status` section to track progress.

Each plan should also get a matching task in FocusAnalyze's "Study: Neuroscience" project.

## Rebuilding the viewer after code changes

`docker-compose.yml` does not mount `viewer/` into the `viewer` container — it's a full
production build (webpack, via `viewer/Dockerfile`), unlike `backend`/`frontend` which are
bind-mounted and pick up changes live. Any edit under `viewer/` (extensions, modes, platform/app,
etc.) needs an explicit rebuild + restart before it's visible in the browser:

```
docker compose build viewer && docker compose up -d viewer
```

This is a full monorepo webpack build and can take several minutes — run it in the background
and check back rather than blocking on it. Do this automatically whenever `viewer/` source
changes as part of a task, without waiting to be asked.

Verifying a viewer change deployed correctly is not just "container is Up" — confirm the new
code is actually in the served bundle. `viewer/.docker/compressDist.sh` precompresses static
assets and **truncates the plain (non-`.gz`) files to 0 bytes**, relying on nginx's
`gzip_static` to serve the `.gz` version — so `grep`ing the plain `.js` files in the built image
will find nothing even when the code is present. Check via the gzipped file instead, e.g.:

```
docker compose exec -T viewer sh -c "gunzip -c /usr/share/nginx/html/app.bundle.*.js.gz | grep -o '<string to check for>'"
```

There is no browser-automation tool in this environment — server-side checks (routes 200,
new code present in the bundle) confirm deployment, but actual client-side/React behavior
(redirects, auth state, etc.) needs a manual check in a real browser. Say so explicitly rather
than claiming a UI flow works based on server-side checks alone.
