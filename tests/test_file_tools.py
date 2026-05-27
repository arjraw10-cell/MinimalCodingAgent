import os
import pytest
from src.tools.file_tools import Workspace, change_workspace, read_file, write_file, edit_file

@pytest.fixture(autouse=True)
def setup_workspace(tmp_path):
    # Save the original working directory
    original_cwd = Workspace.current_dir
    # Set the workspace to a temporary directory for tests
    Workspace.current_dir = str(tmp_path)

    yield tmp_path

    # Restore after the test
    Workspace.current_dir = original_cwd

def test_change_workspace(tmp_path):
    new_dir = tmp_path / "new_workspace"
    new_dir.mkdir()

    result = change_workspace(str(new_dir))
    assert "Workspace changed to" in result
    assert Workspace.current_dir == str(new_dir)

def test_write_and_read_file():
    write_result = write_file("test.txt", "Hello, World!")
    assert "Successfully wrote to" in write_result

    read_result = read_file("test.txt")
    assert read_result == "Hello, World!"

def test_paths_relative_to_workspace(tmp_path):
    # Create a sub-directory and change workspace
    sub_dir = tmp_path / "sub"
    sub_dir.mkdir()
    change_workspace(str(sub_dir))

    # Write a file using a relative path
    write_file("nested.txt", "Nested content")

    # Check that it actually was created in sub_dir
    assert (sub_dir / "nested.txt").exists()

    # Read it back using relative path
    read_result = read_file("nested.txt")
    assert read_result == "Nested content"

    # Change back to root and try to read relative to new workspace
    change_workspace(str(tmp_path))
    err_read = read_file("nested.txt")
    assert "Error:" in err_read

def test_edit_file_success():
    write_file("edit.txt", "This is a test file.")
    result = edit_file("edit.txt", "test", "demo")

    assert "Successfully edited" in result
    content = read_file("edit.txt")
    assert content == "This is a demo file."

def test_edit_file_error_not_found():
    write_file("edit.txt", "This is a test file.")
    result = edit_file("edit.txt", "missing", "found")

    assert "Error: old_string not found in file." in result
    content = read_file("edit.txt")
    assert content == "This is a test file."

def test_edit_file_error_multiple_found():
    write_file("edit.txt", "apple apple apple")
    result = edit_file("edit.txt", "apple", "orange")

    assert "Error: old_string found 3 times" in result
    content = read_file("edit.txt")
    assert content == "apple apple apple"

def test_read_non_existent_file():
    result = read_file("does_not_exist.txt")
    assert "Error:" in result
