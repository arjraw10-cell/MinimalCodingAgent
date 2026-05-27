# PiClone - Minimal Python Coding Agent

## Current State
- **Status:** Initial V1 Implementation Complete.
- **Core capabilities:** Async core agent loop, file manipulation, and stateful terminal execution.
- **UI:** Fully integrated Textual-based CLI for seamless chatting.
- **Testing:** 100% passing test suite for tools using `pytest`.

## Tech Stack
- **Language:** Python
- **LLM Provider:** OpenAI API (`openai` package)
- **UI:** `textual`
- **Testing:** `pytest`, `pytest-asyncio`
- **Config:** `python-dotenv`

## Key Commands
- **Run the agent:** `python src/main.py`
- **Run the tests:** `python -m pytest tests/`

## Design Philosophies
1. **Minimalism:** The entire agent, system prompt, and tool definitions are kept as small and efficient as possible (targeting ~1k tokens overhead).
2. **Loud Errors:** The agent must never fail silently. Tool exceptions are caught and explicitly returned as string error messages to the LLM so it can correct its behavior immediately.
3. **Strict Editing:** File edits use strict find-and-replace (`old_string` must be exactly unique).
4. **Statefulness:** Terminals remain persistent to preserve state (like `cd` and ENV vars) between commands.