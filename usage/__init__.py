"""Usage event normalization utilities.

This package defines the logical UsageEvent schema (Plan 013/014) and mapping helpers
that turn concrete sources (ccusage JSONL, routing events, CLIProxy traces) into a
single typed model. Downstream services (sentinel, analytics, recommender) consume
these normalized events.
"""

