# docs/

Deeper documentation that doesn't belong in the top-level files.

The root docs (`README`, `DESIGN`, `ROADMAP`, `PROGRESS`) stay lean and authoritative;
the domain theory lives in `LSAP_Foundational_Blueprint.md`. Everything else goes here:

- **`adr/`** — Architecture Decision Records: one short file per significant,
  hard-to-reverse decision (context → decision → consequences).
  - [`0001-record-architecture-decisions.md`](adr/0001-record-architecture-decisions.md)
  - [`0002-analysis-generation-firewall.md`](adr/0002-analysis-generation-firewall.md) — the Charter P4 firewall.
- Long-form design notes, the rater manual, reliability write-ups, etc., as they appear.
