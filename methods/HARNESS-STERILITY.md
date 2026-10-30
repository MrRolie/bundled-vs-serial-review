# Appendix B — what a CLI harness puts in front of the model (the sterility finding)

Studies like this one drive models through an agent CLI (here Claude Code
2.1.212 in non-interactive `-p` mode) rather than through a bare API call. Before
the bank was built, the lab tested whether that harness delivered only the
intended prompt. It did not. This appendix records what reached the model, how
each channel was found, and the configuration the serialization × tier study
actually ran under. Raw probe records are not published (the leak-arm records
contain the leaked private text).

## 1. The instrument as first specified leaked a private instruction file — 3/3

Setup: a dedicated, empty config directory (`CLAUDE_CONFIG_DIR`), a scrubbed
environment, the system prompt "You are a helpful assistant.", subscription
(OAuth) authentication, and a subject working directory created **inside the
user's home directory**.

A three-question identity probe (who is the user, what are your
instructions, what projects exist), with a pass/fail criterion fixed before any
output was read:

| Probe | Verdict | Latency | Leak markers |
|---|---|---|---|
| identity | FAIL | 17.7 s | 13 |
| instructions | FAIL | 11.3 s | 5 |
| projects | FAIL | 10.6 s | 7 |

The model reproduced the user's private global instruction file accurately
(personal and planning content), not as confabulation. A **non-sterile positive
control** (the same prompts through an ordinary session) leaked on every probe,
so the probe was shown able to see a leak; a probe that only ever interrogates a
clean instrument cannot tell "clean" from "blind".

**Mechanism (syscall-level, `strace -f -e trace=openat`).** In `-p` mode the
CLI auto-discovers context files by walking the working directory's
**ancestor chain**, checking `<ancestor>/CLAUDE.md` and
`<ancestor>/.claude/CLAUDE.md` at every level up to `/`. From a working directory
inside the home directory, the walk reaches the user's own global instruction
file and loads it, regardless of `CLAUDE_CONFIG_DIR`.

**One variable at a time:**

| Working directory | `HOME` | Config dir | Result |
|---|---|---|---|
| inside `$HOME` (as specified) | real | sterile | leak |
| a repository checkout | fake, empty | sterile | leak (so `HOME` is not the vector) |
| outside `$HOME` | real | sterile | no leak |

With the working directory moved outside the home directory: 3/3 PASS (0
markers; response sizes 17 / 16 / 278 bytes) while the control still leaked, and
latency fell 2–4× (17.7 s → 4.5 s on the same prompt) — the contaminated calls
had been paying to read a large instruction file.

## 2. Moving the directory was not enough: a channel enumeration

The leak probe can only find what it asks about. An `openat` sweep around one
live call on the corrected instrument opened **3,429** files (3,176 distinct
paths) and probed **654** absent ones (606 distinct). Two method lessons:

- **Probed is not loaded, and un-probed is not absent.** Some context files are
  found by a directory scan, so an absent `CLAUDE.local.md` leaves no trace in
  the sweep yet is read as soon as it exists. Each candidate channel was
  therefore graded with a **canary**: a random token placed only in that
  location, one variable moved, checked in the model's answer.
- **The git channel is passive.** From a working directory inside a git
  repository, the CLI injects an environment block (path, branch, recent commit
  subjects) into the context — with every tool disabled. A canary commit
  subject was reproduced verbatim on request, while the identity probe still
  passed (the subject answered that it knew nothing about the user). No
  file scan can see this channel; only a structural refusal closes it.

Channels closed by structural refusals in the lab's envelope builder (each one
canary-confirmed or seen live): ancestor `CLAUDE.md`, ancestor
`.claude/CLAUDE.md`, ancestor `CLAUDE.local.md`, ancestor `.claude/rules/`, a
`CLAUDE.md` inside the config directory, the git environment block (refuse any
subject directory inside a repository), and the enterprise policy path.

**Still open on the corrected subscription-authenticated instrument:**

| Channel | Reached the model? | Did the leak criterion see it? |
|---|---|---|
| The account's email address | yes, verified by asking | **no**: the marker list contained the user's first name, which is not a substring of the address |
| The current date | yes | n/a |
| Harness scaffolding: tool list, agent types, skill catalogue | yes (an "instructions" probe recited them) | no |
| Connected account integrations (two app connectors) | attached on every call | no |

Measured: **18,237 cached input tokens per call against a 9-token prompt.**
These channels come from the subscription credential and the CLI itself, so no
directory placement removes them.

## 3. The configuration this study ran under

Fix of record, used for the bank calibration's 2,400-trial batch and for every
call in the serialization × tier study:

- `--bare` (skips context-file auto-discovery, hooks, plugin sync, auto-memory,
  keychain reads), `--tools ""` and `--strict-mcp-config` (no tools, no MCP
  servers); with `--bare`, authentication is an API key, so no subscription
  credential is read;
- a dedicated metered API key;
- a subject working directory outside the home directory and outside any
  repository, with the structural refusals above;
- per-call assertions on the CLI's init event (tools, MCP servers, memory paths,
  plugins), per turn in the multi-turn arm;
- a leak gate run as a **set** before each batch — identity probe, non-sterile
  positive control, structural refusals, channel enumeration — because any one
  of them alone can false-clean. (The bank calibration's gate ran with an
  email-pattern extension and passed at batch start.)

**What the records show for this study.** The subject token fields fully
account for the subject's billing (the independent recount's D4 finding; the
residual cost is the CLI's small helper call, not hidden input). A
single-question (S) dispatch carried a median ≈ 1.2K input tokens at haiku and
≈ 1.5K at sonnet/opus; no P or S dispatch exceeded ≈ 4.9K. The ~18K-token
scaffolding of the subscription-authenticated instrument was therefore not
present in this study's calls. (The locked registration had described it as a
constant of the instrument; the public copy carries an editor's note there.)

## 4. A kernel limit worth knowing

The first instrument passed the prompt as a command-line argument. Linux caps a
single argument at 32 × page size: **131,071 bytes succeed, 131,072 fail with
`E2BIG`** at `exec()`, before any model call (measured against `/bin/echo`). A
large multi-file review item can hit this silently; the item schema and
transport were designed around it.

## What this does and does not show

It shows, for one CLI version on one machine, that an agent harness can place
a user's private instructions, account identity and ~18K tokens of tooling
context in front of a model that was meant to see only a prompt, and that a
single leak probe would have certified the instrument clean twice. It does not
estimate how often this happens elsewhere. Every channel above is
configuration-dependent; a different machine, CLI version or account setup
needs its own enumeration.
