# Error Diagnostics and Repair Workflow

**Invocation**: You can invoke this workflow by asking the AI assistant to "run the repair workflow" or "troubleshoot this error".

## Purpose
To systematically diagnose recurring or complex errors, understand historical context (what has already been tried), and formulate a safe, minimally-disruptive resolution plan. This prevents the AI from getting stuck in a loop of failed attempts or blindly trying fixes without context.

## Workflow Steps for AI Agent

When invoked, the AI must strictly follow these steps sequentially:

### 1. Gather Error Context
- **Read Error Logs**: Request the latest error output from the user or read relevant log files (e.g., from the terminal or console).
- **Identify the Failure**: Pinpoint the exact error message, stack trace, and the specific component or file failing.

### 2. Review Past Repair Attempts
- **Consult Git History**: Run `git log` and `git show` on the failing files to understand recent modifications.
- **Consult Task/Plan Context**: Review `task.md` and `implementation_plan.md` to see the documented intent behind recent changes.
- **Analyze Previous Fixes**: Identify what approaches have already been attempted for this specific error and *why* they failed. Document this internally to avoid repeating mistakes.

### 3. Root Cause Analysis
- Cross-reference the error and the past attempts against the architecture (`docs/architecture.md`) and governance rules (`AI_GOVERNANCE.md`).
- Formulate a clear hypothesis for the root cause of the error.
- Verify the hypothesis against the codebase (e.g., check if an imported function actually exists, or if a variable is being mutated incorrectly).

### 4. Formulate a Resolution Plan
- Create or update the `implementation_plan.md` file detailing the proposed fix.
- Ensure the fix aligns with **Rule 2: Cautious Implementation** (make isolated, incremental, minimally disruptive changes).
- Avoid broad refactors or architectural drift.
- Include a specific "Verification Plan" outlining how to test the fix (e.g., unit test, manual UI step, terminal command).

### 5. Request User Approval (STOP)
- Present the hypothesis and the resolution plan to the user.
- **CRITICAL**: Stop execution and ask for explicit user approval before proceeding to write any code or execute any commands.

---
*By following this workflow, we ensure stability over recreation and adhere to our AI Governance principles.*
