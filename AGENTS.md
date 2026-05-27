# Agent Architecture & Tools

## 1. Core Agent Loop (`src/agent.py`)
The AI operates on an asynchronous `while` loop that interfaces with the OpenAI API:
1. Appends the latest user message to the context.
2. Calls OpenAI with the appended context and tool schemas.
3. If the model streams text, it yields it back to the UI thread via a callback.
4. If the model issues a `tool_call`, it safely parses the JSON, executes the corresponding Python function, catches any errors, and returns the result back to the context.
5. The loop repeats until the model produces a final text output with no tool calls.

## 2. Terminal Tools (`src/tools/terminal_tools.py`)
Provides stateful terminal execution natively bridging LLMs to the shell.
- **Persistent Shells:** Wraps OS-specific shells (`cmd.exe` or `/bin/bash`) using `asyncio.create_subprocess_shell`.
- **Blocking Mode:** For immediate commands where state (like `cd`) matters. The agent appends a unique UUID sentinel (`__CMD_DONE_...__`) to the command. It reads `stdout` asynchronously until it hits the sentinel, ensuring it captures the full output and knows exactly when the command finished.
- **Background Mode:** For long-running processes (e.g., starting a web server). A background task continually reads `stdout`/`stderr` into an in-memory list. The agent uses `read_logs(terminal_id, start_line, end_line)` to slice and inspect the output when needed.

## 3. File Tools (`src/tools/file_tools.py`)
A highly constrained file manipulation interface designed to prevent LLM hallucinations.
- **Workspace State:** Maintains a global `Workspace` (starting at `os.getcwd()`). All subsequent file paths resolve relative to this. `change_workspace` allows the agent to navigate.
- **Loud Errors:** Missing files or permission errors return explicit error strings rather than crashing the process.
- **Strict Find-and-Replace:** The `edit_file(path, old_string, new_string)` tool strictly requires `old_string` to appear exactly **once**. If it appears 0 times or >1 time, it throws a loud error forcing the agent to request more specific context.