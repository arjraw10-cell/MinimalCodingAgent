import asyncio
import sys
import uuid
import traceback
from typing import Dict, List, Optional, Any

class TerminalSession:
    def __init__(self, terminal_id: str, background: bool):
        self.terminal_id = terminal_id
        self.background = background
        self.process: Optional[asyncio.subprocess.Process] = None
        self.logs: List[str] = []
        self.log_task: Optional[asyncio.Task] = None

terminals: Dict[str, TerminalSession] = {}

async def new_terminal(background: bool) -> str:
    try:
        terminal_id = str(uuid.uuid4())
        session = TerminalSession(terminal_id, background)

        # Determine appropriate shell based on OS
        shell = "cmd.exe" if sys.platform == "win32" else "/bin/bash"

        session.process = await asyncio.create_subprocess_shell(
            shell,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        if background:
            session.log_task = asyncio.create_task(_read_logs_loop(session))

        terminals[terminal_id] = session
        return terminal_id
    except Exception as e:
        return f"Error creating terminal: {str(e)}\n{traceback.format_exc()}"

async def _read_logs_loop(session: TerminalSession):
    try:
        while True:
            line = await session.process.stdout.readline()
            if not line:
                break
            try:
                decoded = line.decode('utf-8', errors='replace').rstrip('\r\n')
                session.logs.append(decoded)
            except Exception:
                pass
    except Exception:
        pass

async def execute_command(terminal_id: str, command: str, background: bool, timeout: int = None) -> str:
    try:
        if terminal_id not in terminals:
            return f"Error: Terminal {terminal_id} not found."

        session = terminals[terminal_id]

        if session.background != background:
            return f"Error: Terminal {terminal_id} was created with background={session.background}, but execute_command called with background={background}."

        if background:
            # For background terminals, just write the command and return
            cmd_bytes = f"{command}\n".encode('utf-8')
            session.process.stdin.write(cmd_bytes)
            await session.process.stdin.drain()
            return f"Command started in background terminal {terminal_id}."
        else:
            # For blocking terminals, append a sentinel and wait for it
            sentinel = f"__CMD_DONE_{uuid.uuid4().hex}__"
            full_cmd = f"{command}\necho {sentinel}\n"

            session.process.stdin.write(full_cmd.encode('utf-8'))
            await session.process.stdin.drain()

            output_lines = []

            async def _read_until_sentinel():
                while True:
                    line = await session.process.stdout.readline()
                    if not line:
                        break
                    decoded = line.decode('utf-8', errors='replace').rstrip('\r\n')

                    # On Windows, commands echo by default unless @echo off.
                    # By checking if the stripped line is exactly the sentinel,
                    # we match the output of `echo {sentinel}` and NOT the echoed command.
                    if decoded.strip() == sentinel:
                        break

                    output_lines.append(decoded)

            if timeout is not None:
                await asyncio.wait_for(_read_until_sentinel(), timeout=timeout)
            else:
                await _read_until_sentinel()

            return "\n".join(output_lines)
    except asyncio.TimeoutError:
        return "Error: Command timed out."
    except Exception as e:
        return f"Error executing command: {str(e)}\n{traceback.format_exc()}"

async def read_logs(terminal_id: str, start_line: int = 0, end_line: int = None) -> str:
    try:
        if terminal_id not in terminals:
            return f"Error: Terminal {terminal_id} not found."

        session = terminals[terminal_id]
        if not session.background:
            return f"Error: Terminal {terminal_id} is not a background terminal."

        logs = session.logs
        if end_line is None:
            end_line = len(logs)

        if start_line < 0:
            start_line = 0

        selected_logs = logs[start_line:end_line]

        if not selected_logs:
            return "No logs available for the specified range."

        result = []
        for i, line in enumerate(selected_logs, start=start_line):
            result.append(f"{i}: {line}")

        return "\n".join(result)
    except Exception as e:
        return f"Error reading logs: {str(e)}\n{traceback.format_exc()}"

async def close_terminal(terminal_id: str) -> str:
    try:
        if terminal_id not in terminals:
            return f"Error: Terminal {terminal_id} not found."

        session = terminals.pop(terminal_id)
        if session.log_task:
            session.log_task.cancel()

        if session.process:
            try:
                if session.process.stdin:
                    session.process.stdin.close()
                session.process.terminate()
                await asyncio.wait_for(session.process.wait(), timeout=2.0)
            except Exception:
                try:
                    session.process.kill()
                    await asyncio.wait_for(session.process.wait(), timeout=2.0)
                except Exception:
                    pass

        return f"Terminal {terminal_id} closed."
    except Exception as e:
        return f"Error closing terminal: {str(e)}\n{traceback.format_exc()}"

TERMINAL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "new_terminal",
            "description": "Creates a new persistent shell terminal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "background": {
                        "type": "boolean",
                        "description": "If true, creates a background terminal that reads logs asynchronously. If false, creates an interactive blocking terminal."
                    }
                },
                "required": ["background"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Executes a command in a persistent shell terminal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "terminal_id": {
                        "type": "string",
                        "description": "The ID of the terminal to execute the command in."
                    },
                    "command": {
                        "type": "string",
                        "description": "The command to execute."
                    },
                    "background": {
                        "type": "boolean",
                        "description": "Must match the terminal's background property."
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Optional timeout in seconds for blocking commands."
                    }
                },
                "required": ["terminal_id", "command", "background"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_logs",
            "description": "Reads logs from a background terminal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "terminal_id": {
                        "type": "string",
                        "description": "The ID of the background terminal."
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "The line number to start reading from."
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "The line number to end reading at (exclusive)."
                    }
                },
                "required": ["terminal_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_terminal",
            "description": "Closes a persistent shell terminal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "terminal_id": {
                        "type": "string",
                        "description": "The ID of the terminal to close."
                    }
                },
                "required": ["terminal_id"]
            }
        }
    }
]
