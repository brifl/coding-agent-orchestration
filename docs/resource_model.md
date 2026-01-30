# Resource Model

This document defines the resource model for the Vibe project, outlining where different resources live, the precedence rules for resolving them, and the overall discovery order.

## Resource Locations

There are two primary locations for resources:

- **Global:** `~/.<agent>/` - This is the user-level directory where resources are installed for a specific agent. This allows for sharing skills and prompts across different projects.
- **Repo-Local:** `.vibe/` - This is the project-level directory where resources specific to the current repository are stored. This allows for project-specific customizations and overrides.

## Precedence and Discovery Order

The resource discovery mechanism follows a specific order of precedence to resolve resource conflicts. The order is as follows:

1.  **Repo-Local (`.vibe/`)**: Resources in the repository's `.vibe/` directory always take the highest precedence. This allows projects to override global settings and resources with their own versions.
2.  **Global (`~/.<agent>/`)**: If a resource is not found in the repo-local directory, the global agent-specific directory is checked.
3.  **Built-in**: If a resource is not found in either the repo-local or global directories, the system may fall back to a set of built-in default resources.

This precedence order can be summarized as: **Repo-Local > Global > Built-in**.

## Covered Resources

This resource model applies to the following types of resources:

- **Skills**: Reusable capabilities that can be invoked by agents.
- **Prompts**: Templates for generating prompts for agents.
- **Config**: Configuration files that control the behavior of the Vibe workflow, such as `.vibe/config.json`.
- **State**: The current state of the workflow, stored in `.vibe/STATE.md`.

## .gitignore Strategy

To avoid versioning user-specific or generated files, the following `.gitignore` strategy is recommended:

- **`.vibe/`**: This directory should be added to the repository's `.gitignore` file. This prevents project-specific state, history, and context from being committed to the repository. If a project requires versioning of its workflow state, this line can be removed from `.gitignore`.
- **Global resources (`~/.<agent>/`)**: These resources are located in the user's home directory and are not part of any specific repository, so they are not and should not be versioned with the project.
