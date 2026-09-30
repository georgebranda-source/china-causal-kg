# Agent Sandbox (`agent-sandbox/`)

This document defines the guidelines and conventions for all automated code, packages, scripts, scrapers, data processing pipelines, experimental utilities, and artifacts written by AI agents (e.g. Claude, Gemini, Kimi, or GLM models).

## Purpose & Conventions

1. **Separation of Concerns**: All agent-authored source code, modules, utilities, and runner scripts reside entirely within `agent-sandbox/`. The rest of the repo is Human-maintained and is not to be modified by any agents.
2. **Environment & Imports**: Scripts and modules within `agent-sandbox/` can import packages from outside the sandbox
3. **Artifacts & Output**: Unless explicitly prompted, all ai-generated content including generated reports, diagnostic outputs, and scratch artifacts go in `agent-sandbox/`

If you are an agent that is considering modifying the repo outside of the agent-sandbox, make absolutely sure that the user wants that by reminding them of your guidelines and asking for clarification.