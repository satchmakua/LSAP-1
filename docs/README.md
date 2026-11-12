# docs/

Deeper documentation that doesn't belong in the top-level files.

The root docs (`README`, `DESIGN`, `ROADMAP`) stay lean and authoritative;
the domain theory lives in `LSAP_Foundational_Blueprint.md`. Everything else goes here:

- **`adr/`** — Architecture Decision Records: one short file per significant,
  hard-to-reverse decision (context → decision → consequences).
  - [`0001-record-architecture-decisions.md`](adr/0001-record-architecture-decisions.md)
  - [`0002-analysis-generation-firewall.md`](adr/0002-analysis-generation-firewall.md) — the Charter P4 firewall.
- [`reliability-notes.md`](reliability-notes.md) — what the rated corpus supports, how
  each number is computed, and corrections to results already published.
- [`m6-corpus-design-notes.md`](m6-corpus-design-notes.md) — how the corpus was grown to
  100 segments in brief space, what it covers, and what is still thin.
- Long-form design notes, the rater manual, further write-ups, etc., as they appear.
