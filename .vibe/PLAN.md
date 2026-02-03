# PLAN

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## How to use this file

- This is the **checkpoint backlog**.
- Each checkpoint must have: Objective, Deliverables, Acceptance, Demo commands, Evidence.
- Keep checkpoints small enough to complete in one focused iteration.
- Completed stages are archived to `.vibe/HISTORY.md`.

---

## Stage 14 — Skill Sets

**Stage objective:**
Enable named collections of skills that can be deployed together, simplifying configuration and ensuring compatibility.

### 14.0 — Skill set schema

* **Objective:**
  Define how skill sets are structured and stored.

* **Deliverables:**

  * `docs/skill_sets.md` — schema and usage documentation
  * `skillsets/` directory for set definitions
  * Set format: name, description, skills list, version constraints

* **Acceptance:**

  * Sets can reference skills by name with optional version pins
  * Sets can extend other sets (inheritance)

* **Demo commands:**

  * `cat skillsets/vibe-core.yaml`

* **Evidence:**

  * Example skill set with multiple skills

---

### 14.1 — Skill set resolution

* **Objective:**
  Resolve skill sets to concrete skill lists.

* **Deliverables:**

  * `skillctl.py` enhancement: `resolve-set` command
  * Dependency resolution (skill A requires skill B)
  * Conflict detection (incompatible versions)

* **Acceptance:**

  * `skillctl resolve-set vibe-core` outputs resolved skill list
  * Circular dependencies detected and reported

* **Demo commands:**

  * `python tools/skillctl.py resolve-set vibe-core --format json`

* **Evidence:**

  * Resolution output with dependency tree

---

### 14.2 — Bootstrap with skill sets

* **Objective:**
  Enable bootstrapping with a skill set reference.

* **Deliverables:**

  * `bootstrap.py` enhancement: `--skillset <name>` flag
  * Auto-install all skills in set
  * Record set reference in `.vibe/config.json`

* **Acceptance:**

  * `bootstrap.py init-repo . --skillset vibe-core` installs all vibe-core skills
  * Config records which set was used

* **Demo commands:**

  * `python tools/bootstrap.py init-repo /tmp/test --skillset vibe-core`

* **Evidence:**

  * New repo with all skills from set installed

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
