# AI GOVERNANCE & OPERATIONAL CONSTRAINTS (CRITICAL)
All AI agents MUST strictly adhere to:
1. **Maintenance over Recreation**: Enforce stability. Repair and extend existing systems; do not replace or redesign unless explicitly requested.
2. **Cautious Implementation**: Make isolated, incremental, minimally disruptive changes. Minimize architectural drift and unrelated refactors. Never use technical debt as permission for broad rewrites.
3. **Planning & Evidence**: Create implementation plans before coding. Do not invent requirements or logic not supported by evidence.
4. **Validation & Safety**: Require functional, regression, and browser testing. Never assume mocked success. Preserve state consistency. AI answers must NEVER override confirmed user info.
5. **No Looping**: Stop and ask the user if you fail repeatedly; do not loop uncontrollably.

## Knowledge Base Pointers
If you need specific context, `read_file` the relevant documentation:
- **UI & CSS Patterns**: `docs/ui_guidelines.md` (Always query `modern-web-guidance` plugin for CSS decisions)
- **Architecture & Tech Stack**: `docs/architecture.md`
- **Testing Strategy & Tools**: `docs/testing.md`
- **Coding Standards**: `docs/coding_standards.md`

Before starting any task, read the main project intelligence file: `CLAUDE.md`.
