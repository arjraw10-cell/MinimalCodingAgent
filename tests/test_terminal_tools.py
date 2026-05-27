import pytest
import asyncio
import pytest_asyncio
import sys

from src.tools.terminal_tools import (
    new_terminal,
    execute_command,
    read_logs,
    close_terminal,
    terminals
)

@pytest_asyncio.fixture(autouse=True)
async def cleanup_terminals():
    # Clear terminals before each test
    terminals.clear()
    yield
    # Clean up terminals after each test
    for t_id in list(terminals.keys()):
        await close_terminal(t_id)

@pytest.mark.asyncio
async def test_blocking_terminal():
    # Test spawning a blocking terminal, running a command, getting output.
    terminal_id = await new_terminal(background=False)
    assert not terminal_id.startswith("Error")

    # We should be able to run a simple command
    # Use "echo test" which is cross-platform
    output = await execute_command(terminal_id, "echo hello", background=False, timeout=5)

    assert "Error" not in output
    assert "hello" in output.lower()

    # Clean up
    close_result = await close_terminal(terminal_id)
    assert "closed" in close_result

@pytest.mark.asyncio
async def test_background_terminal():
    # Test spawning a background terminal, running a command, reading logs.
    terminal_id = await new_terminal(background=True)
    assert not terminal_id.startswith("Error")

    # Run a command in background
    cmd_result = await execute_command(terminal_id, "echo background_test", background=True)
    assert "Command started" in cmd_result

    # Allow some time for the command to execute and logs to be read
    await asyncio.sleep(1)

    # Read logs
    logs = await read_logs(terminal_id, start_line=0)
    assert "Error" not in logs
    assert "background_test" in logs.lower()

    # Clean up
    close_result = await close_terminal(terminal_id)
    assert "closed" in close_result
