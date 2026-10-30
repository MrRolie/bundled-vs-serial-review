# Order of events — private references

The study ran in a private repository. Its git history is the only evidence
that the plan was locked before the data existed, and that history is not
published. **Lock-before-data is therefore attested here only by private commit
hashes and dates, which an outside reader cannot verify.** If the history is
published later, every line below can be checked against it, and the locked
documents can be checked against the hashes in the second table.

## Commits (private repository, times in -0400)

| When | Commit | Event |
|---|---|---|
| 2026-08-17 14:48 | `4b4ddfd` | independent pre-lock review returns LOCKABLE |
| 2026-08-17 14:51 | `87c569f` | referee-simulation RNG fix (values of record, see amendment) |
| 2026-08-17 15:03 | `7bbe83e` | **registration LOCKED (rev 2.4)** |
| 2026-08-17 15:06 | `79ce12b` | amendment: the five family definitions (locked referent was empty) |
| 2026-08-17 15:08 | `9e23da7` | amendment: referee-simulation values re-pinned |
| 2026-08-21 19:49 | `9e39df6` | parser golden-master vectors (last revision) |
| 2026-08-21 20:49–20:57 | `2ae9449`, `61ba7f4`, `e9b84fe`, `a917dff` | audit certification, key table, shortcut-gate (ZC) scores, question overlay + briefing |
| 2026-08-21 21:28 | `7a9f0f6` | structural-covariate manifest |
| 2026-08-21 21:42 | `d76feb1` | **materials FREEZE completed (§5.7)**: C44 list, selection trace and the calibration-probe record |
| 2026-08-22 14:03 | `bb067fe` | amendment: opus r = 3 → 4, before any opus trial |
| 2026-08-22 18:19 | `0bdfde6` | **haiku trials committed (1,680 records) — first trial data** |
| 2026-08-22 18:45 | `e13bd4c` | sonnet trials committed (924 records) |
| 2026-08-22 19:17 | `d658edd` | opus trials committed (1,056 records) |
| 2026-08-22 19:37 | `88d969d` | adjudication charge, adjudicator system text and arm-guess addendum committed (after all trials; the first lane-1 verdict was written 24 s later, 19:37:41) |
| 2026-08-22 19:53 | `dce5b2f` | J.4 keying-checker charge committed |
| 2026-08-22 20:27 | `36c871b` | first independent recount, blind pass |
| 2026-08-22 20:37–20:41 | `648c9d1`, `addde4d` | first recount report: 978 rows mis-scored MISSING; first table superseded |
| 2026-08-27 23:41:42 | `ad9be8a` | corrected scoring pass rules committed (first corrected-lane verdict written 23:41:48; see the amendment's timing note) |
| 2026-08-28 00:01 | `7e9d89e` | corrected pass executed |
| 2026-08-28 00:36 | `5920136` | independent re-recount, blind pass |
| 2026-08-28 00:44 | `099c5c1` | re-recount report: RECOUNT-AGREES |
| 2026-08-28 01:00–01:03 | `021eaa8`, `59a2b33` | economics recount, blind pass and report |
| 2026-08-28 01:07 | `82913d5` | results certified |

The trial-commit times are when each batch's records were committed. Only the
Sq turns carry timestamps in the records: the earliest is 2026-08-22 14:10:54
-0400 (haiku; trials were block-randomized across arms, so the batch began at
about that time, after the materials freeze and after the opus r = 4
amendment). Those timestamps are not in the public dispatch tables.

## The locked documents (unredacted originals)

| Document | Git blob | SHA-256 |
|---|---|---|
| registration (rev 2.4, at `7bbe83e` and unchanged since) | `d1c70fc2b64dca750e3eb1ec75c4d0e833e4d283` | `a88aa5472a9f6acc17bc4874e6e6d50ed4271620b81b947d31906c66567f02f4` |
| amendment, family definitions (`79ce12b`) | `6dc873efb8e8b1478a8a522567c4215f86c57f7d` | `7e393927efb9a3bc72eb2a5ec0cd42f20dab280dbdae3b10a76c1d5b82d2c545` |
| amendment, simulation of record (`9e23da7`) | `69fdcfd15ebcca8524bbb43eae76bec45fd524fe` | `a554442a67b14732e512c66e803e43e1d609b1cd270e63b5f704471214bc9716` |
| amendment, opus r = 4 (`bb067fe`) | `dd6d6e97cd4178cf7680860caeb9947346c53aa5` | `4e4ff2dfc10fd71a334eb3a551679a47436167047ef9391aeaad3eaac2318338` |

The public copies in this folder are redacted and will not match these
hashes; each one says what kind of text was changed.

## The post-data scoring rules (not part of the lock)

The extraction rules every number of record is computed under (the corrected
scoring pass: the permissive presence grammar, §9's scored text per arm,
text-conditioned retention, and the V2/V3 extraction brackets) were written on
2026-08-27, **after all trial data and after the first, superseded results
table**. They were recorded in the study's private decision ledger, which is
not published; `amendments/2026-08-27-corrected-scoring-pass.md` restates them.

| Document | Git blob | SHA-256 |
|---|---|---|
| private decision ledger at `ad9be8a` (2026-08-27 23:41:42), the file that carries the corrected-pass rules | `3cbc246cd44d616f5644151d211aabd35e5a84d2` | `0c86469ec4722967b1080be0b91252159f813d11017fcb4351d7e4712058998d` |

The ledger also carries the study's other dated rulings and run notes, which
is why it is not published; the hashes let its content at that commit be
checked if the history is published.
