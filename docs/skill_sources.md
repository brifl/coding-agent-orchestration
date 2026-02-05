# Skill sources

## Overview

Skill sources describe where external skills are fetched from and how they are
trusted. Sources can be referenced directly in subscriptions and pinned for
reproducibility.

## Source format

A source can be specified as:
- `git` URL (HTTPS or SSH)
- `github` shorthand (`org/repo`)
- Local filesystem path

Optional fields:
- `ref`: branch, tag, or commit SHA
- `subdir`: subdirectory within the repo containing skills

Example (YAML):

```yaml
source:
  type: git
  url: https://github.com/example/skills
  ref: v1.2.0
  subdir: .codex/skills
```

## Trust levels

Trust levels influence install and update warnings:
- `verified`: known/approved source (no warning by default)
- `community`: community-maintained (warn on install)
- `untrusted`: unknown source (warn on install and update)

## Examples

```yaml
source:
  type: github
  repo: anthropics/skills
  ref: main
  trust: community
```

```yaml
source:
  type: local
  path: ../.codex/skills
  trust: verified
```
