# Governance Model

SokoData follows a **benevolent dictator for now (BDFN)** model transitioning to a **meritocratic community governance** model as the project grows.

## Current Structure

**Maintainer**: Alfred Shingai (project founder)
- Final say on releases, architecture, and security decisions
- Merges PRs after review
- Manages CI/CD and deployments

## Decision Making

### Routine Changes (bug fixes, docs, tests, small features)
- Any contributor can open PR
- Approved by maintainer or designated reviewer
- Merged when CI passes

### Significant Changes (new datasets, API breaking changes, architecture)
- Open RFC issue first (`RFC: <title>`)
- 7-day discussion period
- Consensus sought; maintainer decides if no consensus

### Releases
- Semantic versioning (MAJOR.MINOR.PATCH)
- Maintainer tags releases
- Changelog in `CHANGELOG.md`

## Becoming a Maintainer

Contributors who demonstrate:
- Sustained contributions (3+ merged PRs over 3+ months)
- Deep understanding of codebase and data sources
- Commitment to open data principles
- Good collaboration and review practices

May be invited to become maintainers by consensus of existing maintainers.

## Data Source Policy

All data sources must be:
1. **Open licensed** (CC-BY, CC-BY-IGO, public domain, government open data)
2. **Documented** in dataset `fetch.py` with source URL and license
3. **Provenanced** — every stored record retains `source_url`, `fetched_at`
4. **Reproducible** — ETL must be re-runnable from source

No proprietary, paywalled, or restricted-redistribution sources.

## Security

Security issues reported privately to `alfredshingai@gmail.com`.
Disclosed after fix is deployed (coordinated disclosure).

## Trademark & Branding

"SokoData" name and logo reserved for official distribution.
Forks must use different name unless authorized.

## Transition Plan

When project has 3+ active maintainers from 2+ organizations:
- Form steering committee (3-5 members)
- Decisions by majority vote
- Maintainer role rotates annually
- Adopt formal charter (based on OpenJS Foundation model)