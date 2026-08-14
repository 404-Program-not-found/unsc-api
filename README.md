# UNSC members — static API

Current membership of the UN Security Council, parsed daily from Wikipedia and
published as static JSON on GitHub Pages.

## Endpoints

```txt
/index.json         the 15 sitting members
/incoming           elected for the next year, not yet seated (empty until the June election)
/years/YYYY         composition for that year, 1946–present
/years/index.json   manifest: available years, schema version, generated_at
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
folder `/docs`). Cloudflare fronts it to set the JSON content type.

Order matters when first attaching the domain — GitHub cannot issue its
certificate through Cloudflare's proxy, so the record starts unproxied:

1. Cloudflare DNS: `CNAME  unsc → <user>.github.io`, **DNS only** (grey cloud).
   A `CNAME`, never an `A` record; those are for apex domains.
2. GitHub → Settings → Pages → Custom domain. Wait for the certificate, then
   tick **Enforce HTTPS**. This writes `docs/CNAME`, which the daily job's
   `git add docs` preserves — if it ever vanishes, the domain silently unsets.
3. Switch the record to **Proxied** (orange cloud) and set SSL/TLS to
   **Full (strict)**. Flexible causes a redirect loop against Pages.
4. Rules → Transform Rules → Modify Response Header, filtered on
   `http.host eq "unsc.example.com" and not http.request.uri.path contains "."`:

   | Action | Header | Value |
   | --- | --- | --- |
   | Set static | `content-type` | `application/json` |
   | Set static | `access-control-allow-origin` | `*` |

Verify with
`curl -sSI https://unsc.example.com/current | grep -iE 'content-type|cf-ray'`.
A missing `cf-ray` means the record is grey-clouded and no rule fired.

Only step 4 is load-bearing for correctness: without it every endpoint returns
`application/octet-stream` and browsers download rather than display. The path
filter keeps a future `index.html` from being labelled JSON.

## Known limitation

The permanent-members table is keyed by the year a seat changed hands, so
mid-year transitions land on their start year. `years/1971` shows China and
`years/1991` shows Russia, although the handovers fell in October and December
respectively. This follows the source's own granularity.
