# UNSC members — static API

Current membership of the UN Security Council, parsed daily from Wikipedia and
published as static JSON on GitHub Pages.

## Endpoints

```txt
/            the 15 sitting members
/incoming/   elected for the next year, not yet seated (empty until the June election)
/years/YYYY/ composition for that year, 1946–present
/years/      manifest: available years, schema version, generated_at
```

Example Payload:

```json
{
  "schema_version": 1,
  "generated_at": "2026-08-13T16:01:51Z",
  "source": { "page": "List of members …", "revid": 1363842260 },
  "year": 2026,
  "members": [
    {
      "name": "Republic of Korea",
      "iso3": "KOR",
      "permanent": false,
      "regional_group": "asia_pacific",
      "term_start": 2026,
      "term_end": 2027
    }
  ]
}
```

## Running it

```sh
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env.local     # then set a real contact address
python update.py               # writes docs/
python -m pytest -q
```

Set up `UNSC_API_USER_AGENT` as an env variable before running

## Layout

| Path | Role |
| --- | --- |
| `update.py` | the daily job; parses the current year only |
| `backfill.py` | one-shot, manual; writes `years/1946…`, never runs again |
| `unsc/wikitable.py` | resolves `rowspan`/`colspan` into a dense grid |
| `unsc/countries.py` | country name → ISO 3166 alpha-3 |
| `unsc/guards.py` | refuses to publish a payload that fails its checks |

## Deployment

Pages serves `docs/` from `main` (Settings → Pages → *Deploy from a branch*,
folder `/docs`). Nothing else is required: Pages resolves each directory to its
`index.json` and sends `application/json` on its own, so there is no CDN rule
to keep in sync and no host-specific configuration in the repo.

For a custom domain, order matters — GitHub cannot issue its certificate
through a proxy, so the record starts unproxied:

1. DNS: `CNAME  unsc → <user>.github.io`, **DNS only** if your provider
   proxies. A `CNAME`, never an `A` record; those are for apex domains.
2. GitHub → Settings → Pages → Custom domain. Wait for the certificate, then
   tick **Enforce HTTPS**. This writes `docs/CNAME`, which the daily job's
   `git add docs` preserves — if it ever vanishes, the domain silently unsets.
3. If you then proxy the record, set SSL/TLS to **Full (strict)**. Flexible
   causes a redirect loop against Pages.

Verify with `curl -sSI https://unsc.example.com/ | grep -i content-type`,
expecting `application/json; charset=utf-8`.

## Known limitation

The permanent-members table is keyed by the year a seat changed hands, so
mid-year transitions land on their start year. `/years/1971/` shows China and
`/years/1991/` shows Russia, although the handovers fell in October and December
respectively. This follows the source's own granularity.
