# UNSC members — static API

Current membership of the UN Security Council, parsed daily from Wikipedia and
published as static JSON on GitHub Pages. No server, no database.

## Endpoints

```txt
/current.json      the 15 sitting members
/incoming.json     elected for the next year, not yet seated (empty until the June election)
/years/YYYY.json   composition for that year, 1946–present
/index.json        manifest: available years, schema version, generated_at
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

## Known limitation

The permanent-members table is keyed by the year a seat changed hands, so
mid-year transitions land on their start year. `1971.json` shows China and
`1991.json` shows Russia, although the handovers fell in October and December
respectively. This follows the source's own granularity.
