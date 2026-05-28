# 📋 Task Index

> **Purpose**: Master index of all implementation tasks for the update system.  
> **Usage**: Execute tasks in order within each phase. Tasks are self-contained — each file has all context needed.

---

## How to Use These Tasks

1. Tasks are organized by phase (Phase 0 → Phase 4)
2. Within each phase, execute tasks in numerical order unless dependencies allow parallelism
3. Each task file is **self-contained** — it includes all context, affected files, validation criteria, and reasoning
4. An AI agent should be able to execute any task by reading **only that task file** without scanning unrelated project files
5. Mark tasks as complete by updating the status in this index

---

## Phase 0: Foundation & Infrastructure

| ID | File | Status | Dependencies | Description |
|----|------|--------|-------------|-------------|
| P0-01 | [P0-01_create_update_package.md](./P0-01_create_update_package.md) | ⬜ | None | Create `src/update/` package with scaffolding |
| P0-02 | [P0-02_add_dependencies.md](./P0-02_add_dependencies.md) | ⬜ | None | Add tufup and bsdiff4 to requirements.txt |
| P0-03 | [P0-03_setup_github_actions.md](./P0-03_setup_github_actions.md) | ⬜ | None | Configure GitHub Actions CI/CD workflow |
| P0-04 | [P0-04_initialize_tuf.md](./P0-04_initialize_tuf.md) | ⬜ | P0-03 | Initialize TUF repository and generate keys |
| P0-05 | [P0-05_setup_firebase_hosting.md](./P0-05_setup_firebase_hosting.md) | ⬜ | P0-03 | Set up Firebase Hosting for manifest CDN |
| P0-09 | [P0-09_version_utils.md](./P0-09_version_utils.md) | ⬜ | P0-01 | Implement version_utils.py with semver logic |

## Phase 1: Core Update Logic

| ID | File | Status | Dependencies | Description |
|----|------|--------|-------------|-------------|
| P1-01 | [P1-01_integrity_module.md](./P1-01_integrity_module.md) | ⬜ | P0-01 | Implement SHA-256 verification and integrity checks |
| P1-02 | [P1-02_update_checker.md](./P1-02_update_checker.md) | ⬜ | P0-09, P1-01 | Implement UpdateChecker QThread worker |
| P1-03 | [P1-03_update_manager.md](./P1-03_update_manager.md) | ⬜ | P1-02 | Implement UpdateManager orchestrator |
| P1-04 | [P1-04_rollback_manager.md](./P1-04_rollback_manager.md) | ⬜ | P0-01 | Implement backup, restore, and manifest tracking |
| P1-05 | [P1-05_apply_update_script.md](./P1-05_apply_update_script.md) | ⬜ | P1-04 | Implement apply_update.bat external updater |

## Phase 2: UI Integration & Delivery Pipeline

| ID | File | Status | Dependencies | Description |
|----|------|--------|-------------|-------------|
| P2-01 | [P2-01_update_notification_ui.md](./P2-01_update_notification_ui.md) | ⬜ | P1-02 | Add update notification widget to main_window.py |
| P2-03 | [P2-03_startup_integration.md](./P2-03_startup_integration.md) | ⬜ | P1-02 | Integrate UpdateChecker into main.py bootstrap |

## Phase 3: Security Hardening

| ID | File | Status | Dependencies | Description |
|----|------|--------|-------------|-------------|
| P3-01 | [P3-01_tuf_integration.md](./P3-01_tuf_integration.md) | ⬜ | P1-02 | Integrate tufup TUF metadata verification |

## Phase 4: Polish & Release

| ID | File | Status | Dependencies | Description |
|----|------|--------|-------------|-------------|
| P4-01 | [P4-01_documentation_update.md](./P4-01_documentation_update.md) | ⬜ | All | Update all project documentation |

---

> ⬜ = Not started | 🔄 = In progress | ✅ = Complete | ❌ = Blocked
