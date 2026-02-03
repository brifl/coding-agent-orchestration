# PLAN

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## How to use this file

- This is the **checkpoint backlog**.
- Each checkpoint must have: Objective, Deliverables, Acceptance, Demo commands, Evidence.
- Keep checkpoints small enough to complete in one focused iteration.
- Completed stages are archived to `.vibe/HISTORY.md`.

---

## Stage 15 — Skill Subscription

**Stage objective:**
Enable subscribing to skills from external repositories, with trust, pinning, and auto-update capabilities.

### 15.0 — Subscription sources

* **Objective:**
  Define how external skill sources are specified and trusted.

* **Deliverables:**

  * `docs/skill_sources.md` — source configuration and trust model
  * Source format: git URL, branch/tag, subdirectory path
  * Trust levels: verified, community, untrusted

* **Acceptance:**

  * Sources can be GitHub repos, git URLs, or local paths
  * Trust level affects installation warnings

* **Demo commands:**

  * `cat docs/skill_sources.md`

* **Evidence:**

  * Example source configuration

---

### 15.1 — Subscription and pinning

* **Objective:**
  Implement skill subscription with version pinning.

* **Deliverables:**

  * `skillctl.py` enhancement: `subscribe` command
  * Pin format: `source@version` or `source@commit`
  * Lock file: `.vibe/skill-lock.json`

* **Acceptance:**

  * `skillctl subscribe https://github.com/anthropics/skills skill-name`
  * Lock file records exact versions for reproducibility

* **Demo commands:**

  * `python tools/skillctl.py subscribe https://github.com/anthropics/skills claude-memory --pin v1.0.0`

* **Evidence:**

  * Lock file showing pinned subscription

---

### 15.2 — Subscription sync and update

* **Objective:**
  Enable syncing subscribed skills to latest (or pinned) versions.

* **Deliverables:**

  * `skillctl.py` enhancement: `sync` command
  * Respects pins, warns on major version changes
  * `--upgrade` flag to update pins

* **Acceptance:**

  * `skillctl sync` updates all subscribed skills
  * Breaking changes require explicit `--upgrade`

* **Demo commands:**

  * `python tools/skillctl.py sync`
  * `python tools/skillctl.py sync --upgrade`

* **Evidence:**

  * Sync output showing updates applied

---
