import os
import json

class Workspace:
    current_dir = os.getcwd()

def _resolve_path(path: str) -> str:
    """Helper to resolve path relative to workspace."""
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(Workspace.current_dir, path))

def change_workspace(new_path: str) -> str:
    """Changes the current workspace. Subsequent file operations will be relative to this new path."""
    try:
        abs_path = _resolve_path(new_path)
        Workspace.current_dir = abs_path
        return f"Workspace changed to {abs_path}"
    except Exception as e:
        return f"Error: {str(e)}"

def read_file(path: str) -> str:
    """Reads a file relative to the workspace."""
    try:
        abs_path = _resolve_path(path)
        with open(abs_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error: {str(e)}"

def write_file(path: str, content: str) -> str:
    """Writes to a file relative to the workspace. Creates parent directories if needed."""
    try:
        abs_path = _resolve_path(path)
        dir_name = os.path.dirname(abs_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error: {str(e)}"

def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Reads the file, checks how many times old_string appears. If exactly 1, replace with new_string and save."""
    try:
        abs_path = _resolve_path(path)
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()

        occurrences = content.count(old_string)
        if occurrences == 0:
            return "Error: old_string not found in file."
        elif occurrences > 1:
            return f"Error: old_string found {occurrences} times, must be strictly unique."

        new_content = content.replace(old_string, new_string)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return f"Successfully edited {path}"
    except Exception as e:
        return f"Error: {str(e)}"

# Export a list of OpenAI tool definition dicts
file_tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "change_workspace",
            "description": "Changes the current workspace. Subsequent file operations will be relative to this new path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "new_path": {"type": "string", "description": "The new workspace path"}
                },
                "required": ["new_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads a file relative to the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to read"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Writes to a file relative to the workspace. Creates parent directories if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to write"},
                    "content": {"type": "string", "description": "Content to write to the file"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Reads the file, checks how many times old_string appears. If exactly 1, replace with new_string and save. If 0 or >1, RETURN AN ERROR STRING.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to edit"},
                    "old_string": {"type": "string", "description": "The string to be replaced (must be exactly unique in the file)"},
                    "new_string": {"type": "string", "description": "The new string to replace old_string with"}
                },
                "required": ["path", "old_string", "new_string"]
            }
        }
    }
]