# Security policy

Daybook handles unusually sensitive data. Please report security and privacy issues
privately through a [GitHub security advisory](https://github.com/hr23232323/daybook/security/advisories/new).
Do not include real financial records, bank credentials, SimpleFIN tokens, API keys,
or database files in the report.

You can expect an initial response within seven days. This is a small, volunteer-run
project, so a fix timeline depends on severity and reproducibility.

## Current security model

- Daybook binds to `127.0.0.1` by default and is not designed to be internet-facing.
- The local SQLite database is not encrypted at rest. Your operating system account
  and disk encryption are the current protection for stored records.
- Manual CSV/OFX/QFX imports are processed locally.
- SimpleFIN sync sends requests to the SimpleFIN access URL stored in the local
  database.
- Advisor and coach features send selected financial context to the configured LLM
  endpoint. They are disabled when no LLM key is configured.
- The advisor's database tools are read-only, but its output should still be treated
  as untrusted guidance rather than financial advice.

Please do not deploy the current application to a public host without adding
authentication, transport security, request protections, secret management, and a
careful multi-user data-isolation design.
