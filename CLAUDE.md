# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Collaboration Style

**Do not write implementation files.** Instead, show the user what to write in the chat and explain why, so they can write it themselves. This applies to all source files (`.py`, `.html`, `.js`, etc.). Configuration, docs, and OpenSpec artifacts are the exception — those can be written directly.

## Repository Structure

This is a portfolio monorepo containing independent projects. Each project has its own `pyproject.toml` and `uv.lock` and is managed independently.

## Dependency Management

All projects use `uv`. From within a project directory:

```bash
uv sync          # install dependencies
uv run python main.py   # run with project env
```

## OpenSpec Workflow

This repo uses the OpenSpec spec-driven workflow. Use the `/openspec-propose`, `/openspec-apply-change`, and `/openspec-archive-change` skills to manage changes. Config lives at `openspec/config.yaml`. Completed changes are archived under `openspec/changes/archive/`.
