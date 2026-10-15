"""
===============================================================================
Project Setup Script for Python Development in VSCode
===============================================================================

Description:
    This script automates the creation of a standardized Python project
    structure with virtual environment setup, VSCode configuration,
    editable installation, and essential starter files. It is designed to
    work across Windows, macOS, and Linux, with platform-specific logic
    to handle paths and executables appropriately.

Features:
    - Creates project folder structure
    - Sets up a `.venvs/<project>` isolated virtual environment
    - Installs dependencies from `requirements.txt` or creates an empty one if not found
    - Adds VSCode settings to use the venv interpreter
    - Generates `main.py`, `utils/`, `README.md`, `.gitignore`, and `pyproject.toml`
    - Supports editable installs using setuptools

------------------------------------------------------------------------------
Author:     Pascal Berube
Email:      Pascal_b@hotmail.com
Version:    1.0.0
Date:       2025-07-02
License:    MIT License
Python:     3.13.2
Platform:   Windows, Linux, macOS

===============================================================================
Update Log:
===============================================================================
- [2025-07-02] Initial version with full cross-platform support and setup logic
===============================================================================
"""

import getpass
import json
import os
import platform
import subprocess

import tkinter as tk
from tkinter import filedialog


def choose_directory():
    """
    Open a GUI dialog to let the user select a directory for the new project.

    This function uses tkinter to display a folder selection dialog and returns
    the path chosen by the user. The root window is hidden to avoid displaying
    the main tkinter window.

    Returns:
        str: The absolute path of the selected directory, or an empty string
             if the dialog is cancelled.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main tkinter window
    return filedialog.askdirectory(title="Select directory for the new project")


def get_python_executable(venv_path):
    """
    Get the absolute path to the Python interpreter within the virtual environment.

    This function determines the correct executable path depending on the
    operating system. It assumes standard virtual environment structure:
    - Windows: <venv_path>/Scripts/python.exe
    - Unix-like (Linux/macOS): <venv_path>/bin/python

    Args:
        venv_path (str): The root path to the virtual environment.

    Returns:
        str: Full path to the Python interpreter inside the venv.
    """
    if platform.system() == "Windows":
        # On Windows, the Python executable is in the 'Scripts' subfolder
        return os.path.join(venv_path, "Scripts", "python.exe")
    else:
        # On Linux/macOS, it's located in the 'bin' subfolder
        return os.path.join(venv_path, "bin", "python")


def get_pip_executable(venv_path):
    """
    Get the absolute path to the pip executable within the virtual environment.

    This function detects the current operating system and returns the appropriate
    path to the pip binary inside the given virtual environment:
    - Windows: <venv_path>/Scripts/pip.exe
    - Unix-like (Linux/macOS): <venv_path>/bin/pip

    Args:
        venv_path (str): The root path to the virtual environment.

    Returns:
        str: Full path to the pip executable inside the venv.
    """
    if platform.system() == "Windows":
        # On Windows, pip is located in the 'Scripts' folder
        return os.path.join(venv_path, "Scripts", "pip.exe")
    else:
        # On Linux/macOS, pip resides in the 'bin' folder
        return os.path.join(venv_path, "bin", "pip")


def get_venv_path(base_dir):
    """
    Construct the full path to the virtual environment directory
    based on the project folder name.

    The virtual environment is created in a hidden ".venvs" directory
    inside the user's home folder. The environment is named after
    the project directory (i.e., the last segment of base_dir).

    Example:
        If base_dir = "/home/user/MyProject", the returned path will be:
        "/home/user/.venvs/MyProject"

    Args:
        base_dir (str): The path to the selected project directory.

    Returns:
        str: Full path to the virtual environment (e.g., ~/.venvs/ProjectName).
    """
    # Extract the project name from the base directory
    project_name = os.path.basename(base_dir)

    # Get the user's home directory in a cross-platform way
    home = os.path.expanduser("~")

    # Return the path: ~/.venvs/<project_name>
    return os.path.join(home, ".venvs", project_name)


def create_virtualenv(venv_path):
    """
    Create a new virtual environment at the specified path and upgrade pip.

    If the virtual environment does not already exist at the target location,
    this function will:
        - Use the built-in `venv` module to create a new virtual environment.
        - Automatically upgrade `pip` to the latest version using the
          interpreter inside the newly created environment.

    If the environment already exists, it simply logs that information.

    Args:
        venv_path (str): The full path where the virtual environment should be created.

    Returns:
        None
    """
    if not os.path.exists(venv_path):
        # Create a new virtual environment at the given path
        subprocess.run(["python", "-m", "venv", venv_path])
        print(f"Created virtual environment at: {venv_path}")

        # Upgrade pip using the virtual environment's Python executable
        subprocess.run(
            [
                get_python_executable(venv_path),
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip",
            ]
        )
        print("Upgraded pip in the virtual environment.")
    else:
        # Skip creation if the venv already exists
        print(f"Virtual environment already exists at: {venv_path}")


def install_dependencies(venv_path, project_dir):
    """
    Ensure that a requirements.txt file exists and install dependencies from it.

    This function performs the following steps:
    - Checks if a `requirements.txt` file exists in the project directory.
      If it doesn't, a placeholder file is created with a comment.
    - Installs the dependencies listed in `requirements.txt` using the pip
      executable from the virtual environment.

    Args:
        venv_path (str): The full path to the virtual environment.
        project_dir (str): The path to the root of the project.

    Returns:
        None
    """
    # Path to the requirements.txt file inside the project
    requirements = os.path.join(project_dir, "requirements.txt")

    # Create a default requirements.txt if it doesn't exist
    if not os.path.exists(requirements):
        with open(requirements, "w") as f:
            f.write("# Add your dependencies here\n")
        print(f"Created empty requirements.txt at: {requirements}")

    # Get the platform-specific pip path and install the dependencies
    pip_exe = get_pip_executable(venv_path)
    subprocess.run([pip_exe, "install", "-r", requirements])
    print(f"Installed dependencies from {requirements}")


def setup_vscode_settings(project_dir):
    """
    Create a VSCode settings.json file that points to the virtual environment interpreter.

    This function generates a `.vscode/settings.json` file in the project directory
    with configuration for the Python interpreter path. The path is constructed
    using environment variables so it's portable across different systems.

    The interpreter path is determined as:
        - Windows: ${env:USERPROFILE}\\.venvs\\<project_name>\\Scripts\\python.exe
        - Linux/macOS: ${env:HOME}/.venvs/<project_name>/bin/python

    Args:
        project_dir (str): The root directory of the Python project.

    Returns:
        None
    """
    # Create the .vscode directory if it doesn't already exist
    vscode_dir = os.path.join(project_dir, ".vscode")
    os.makedirs(vscode_dir, exist_ok=True)

    # Path to the VSCode settings.json file
    settings_path = os.path.join(vscode_dir, "settings.json")

    # Determine interpreter path based on platform
    if platform.system() == "Windows":
        venv_relative = f"${{env:USERPROFILE}}\\.venvs\\{os.path.basename(project_dir)}\\Scripts\\python.exe"
    else:
        venv_relative = (
            f"${{env:HOME}}/.venvs/{os.path.basename(project_dir)}/bin/python"
        )

    # Build VSCode settings JSON structure
    settings = {
        "python.defaultInterpreterPath": venv_relative,
        "python.terminal.activateEnvironment": True,
    }

    # Write the settings to settings.json
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=4)

    print(f"Created VSCode settings at: {settings_path}")


def create_utils_module(project_dir):
    """
    Create a 'utils' directory inside the project and make it a Python package.

    This function ensures that a `utils/` subdirectory exists within the given
    project directory. It also adds an empty `__init__.py` file to mark the
    directory as a Python package, enabling module imports.

    Args:
        project_dir (str): The root directory of the Python project.

    Returns:
        None
    """
    # Full path to the utils directory
    utils_dir = os.path.join(project_dir, "utils")

    # Create the utils directory if it doesn't exist
    os.makedirs(utils_dir, exist_ok=True)
    print(f"Created utils directory at: {utils_dir}")

    # Create an empty __init__.py file to make utils a Python package
    init_file = os.path.join(utils_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            pass  # Create an empty file
        print(f"Created __init__.py at: {init_file}")


def create_main_file(project_dir):
    """
    Create a main.py file with basic boilerplate code.

    This function checks if a `main.py` file exists in the project directory.
    If not, it creates one with a simple `main()` function template and a
    standard `if __name__ == "__main__"` guard to serve as the entry point.

    The boilerplate includes commented example code showing how to use a
    function from the `utils` package.

    Args:
        project_dir (str): The root directory of the Python project.

    Returns:
        None
    """
    main_path = os.path.join(project_dir, "main.py")

    if not os.path.exists(main_path):
        with open(main_path, "w") as f:
            f.write(
                """def main():
    pass
    # Example usage of a function from utils
    # Replace with actual function from your utils
    # result = module1.some_function()
    # print(result)

if __name__ == "__main__":
    main()"""
            )
        print(f"Created main.py at: {main_path}")


def create_gitignore(project_dir):
    """
    Create a standard .gitignore file in the project directory.

    This function checks if a `.gitignore` file exists. If it does not, it
    creates one with common patterns to exclude Python virtual environments,
    VSCode workspace settings, and Python cache files from version control.

    Args:
        project_dir (str): The root directory of the Python project.

    Returns:
        None
    """
    gitignore_path = os.path.join(project_dir, ".gitignore")

    # Only create .gitignore if it doesn't exist
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, "w") as f:
            f.write(
                """# Ignore virtual environment
.venv/

# Ignore VSCode settings
.vscode/

# Ignore Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
"""
            )
        print(f"Created .gitignore at: {gitignore_path}")


def get_venv_python_version(venv_path):
    """
    Retrieve the Python version used by the virtual environment.

    This function executes the Python interpreter inside the virtual environment
    with the `--version` flag, captures its output, and parses the version number.
    It returns only the major and minor parts (e.g., "3.10").

    If the command fails for any reason, it returns a default fallback version "3.10".

    Args:
        venv_path (str): The path to the virtual environment directory.

    Returns:
        str: The Python version in 'major.minor' format (e.g., "3.10").
    """
    python_exe = get_python_executable(venv_path)

    # Run '<python_exe> --version' and capture output
    result = subprocess.run([python_exe, "--version"], capture_output=True, text=True)

    if result.returncode == 0:
        # Extract version string from stdout, e.g. "Python 3.10.12"
        version = result.stdout.strip().split()[1]
        # Return major.minor only (e.g. "3.10")
        return ".".join(version.split(".")[:2])
    else:
        # Default/fallback version if detection fails
        return "3.13"


def create_pyproject_toml(project_dir, venv_path):
    """
    Create a pyproject.toml file with editable install configuration and dynamic metadata.

    This function generates a basic `pyproject.toml` file for setuptools-based projects,
    setting the project name to the current system username, version to 0.1, and
    specifying the Python version requirement based on the virtual environment's interpreter.
    It also configures setuptools to find packages starting from the project root.

    If `pyproject.toml` already exists, the function skips creation.

    Args:
        project_dir (str): The root directory of the Python project.
        venv_path (str): The path to the virtual environment directory.

    Returns:
        None
    """
    toml_path = os.path.join(project_dir, "pyproject.toml")

    # Skip if pyproject.toml already exists
    if os.path.exists(toml_path):
        print("pyproject.toml already exists.")
        return

    # Get current system username for project metadata
    username = getpass.getuser()

    # Determine Python version from the virtual environment
    python_version = get_venv_python_version(venv_path)

    # Template content for pyproject.toml
    content = f"""[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "{username}"
version = "0.1"
description = "This project is linked to itself for better usability."
authors = [{{ name = "{username}", email = "you@example.com" }}]
readme = "README.md"
requires-python = ">= {python_version}"

[tool.setuptools.packages.find]
where = ["."]
"""

    # Write the pyproject.toml file
    with open(toml_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Created pyproject.toml at: {toml_path}")


def install_editable_package(venv_path, project_dir):
    """
    Install the current project in editable mode within the virtual environment.

    This function uses pip from the virtual environment to install the project
    directory as an editable package (`pip install -e`), enabling live updates
    during development without reinstalling.

    Args:
        venv_path (str): The path to the virtual environment directory.
        project_dir (str): The root directory of the Python project.

    Returns:
        None
    """
    # Get pip executable from the virtual environment
    pip_exe = get_pip_executable(venv_path)

    # Run pip install -e <project_dir> to enable editable install
    subprocess.run([pip_exe, "install", "-e", project_dir])
    print("Installed the project in editable mode (-e).")


def create_readme(project_dir):
    """
    Create a README.md file with updated project instructions and guidelines.

    This function generates a comprehensive README file that covers:
    - Overview of the project structure and features.
    - Instructions on activating the virtual environment.
    - Optional steps to update pip and install dependencies.
    - Version control recommendations.
    - Suggestions for project customization.
    - Guidance for connecting the project repository to GitHub via VSCode.

    If a README.md file already exists, it will not be overwritten.

    Args:
        project_dir (str): The root directory of the Python project.

    Returns:
        None
    """
    readme_path = os.path.join(project_dir, "README.md")

    # Skip creation if README.md already exists
    if os.path.exists(readme_path):
        print("README.md already exists.")
        return

    # Content for README.md with detailed instructions and notes
    content = """# New Project Structure

## Overview
This project includes a basic structure to help you get started quickly with Python development on VSCode. It is designed to work if your project is local or cloud based. The venv will be installed locally and automatically activated for your project.

### Features:
- Virtual environment setup (`.venv`)
- VSCode project settings (`.vscode/settings.json`)
- Utilities module (`utils/`)
- Main entry point (`main.py`)
- Preconfigured `.gitignore`

## Instructions

1. **Activate the Virtual Environment:**  
    - `ctrl + shift + p`  
    - Search for `select interpreter`  
    - Select your virtual environement. Should be something like: `python 3.XX.X (venv)`  

    If on the bottom right of the VSCode window you see `python 3.XX.X (venv)`, your virtual environement is activated, regardless of what your terminal says.

2. **[Optional] - Update pip**  
`python -m pip install --upgrade pip`

3. **[Optional] - Install Dependencies**  
Use `pip` to install required packages (needs a requirement.txt file to work):  
`pip install -r requirements.txt`

4. **[Optional] - Using Version Control**  
The `.gitignore` file is preconfigured to exclude unnecessary files such as virtual environments and cache files.

## Customization
Feel free to expand the project structure to meet your needs. For example:
- Add a `tests/` folder for unit tests.
- Include additional configuration files as necessary.

## Next Steps
Start building your project by editing `main.py` and adding your code modules in `utils/`.

## Connecting the Repository to GitHub (Optional)
To connect your local repository to GitHub using the **Source Control** tab in VSCode, follow these steps:

1. **Open VSCode and Your Project:**  
- Open **Visual Studio Code**.  
- Click on **File** → **Open Folder...**  
- Select your project folder and click **Open**  

2. **Publish to GitHub:**  
- Open the **Source Control** tab by clicking the **Source Control** icon in the Activity Bar on the side of VSCode.  
- If your project is not yet connected to a GitHub repository, you’ll see an option labeled **Publish to GitHub** in the **Source Control** panel.  
- Click **Publish to GitHub**.  
- VSCode will prompt you to either sign in to your GitHub account (if you're not already signed in) or create a new repository on GitHub.  
- Follow the prompts to create a new GitHub repository and push your project to it.

3. **Create a New Repository on GitHub:**  
- If you choose to create a new repository through VSCode, enter the repository name and any other required details.  
- After filling out the necessary information, click **Publish** to push the repository to GitHub.

4. **Stage Your Changes:**  
- In the **Source Control** tab, you’ll see your untracked files.  
- Click the **+** icon next to the files you want to stage, or click **Stage All Changes** at the top to stage all the files.

5. **Commit Your Changes:**  
- In the **Source Control** tab, enter a commit message in the **Message** box at the top.  
- Click the **✔** icon to commit your changes.

6. **Push to GitHub:**  
- After committing, you’ll see a **Push** icon at the top of the Source Control panel, or you may receive a notification prompting you to push your changes to GitHub.  
- Click the **Push** icon to push your changes to the remote GitHub repository.

7. **Verify the Connection:**  
- Go to your GitHub repository page, and you should see the files from your local project.

Now your project is connected to GitHub, and you can use the **Source Control** tab in VSCode to make commits, stage changes, and push them to your repository.
"""

    # Write README.md content to file
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Created README.md at: {readme_path}")


def setup_python_project(project_dir):
    """
    Orchestrate the full Python project setup process.

    This function runs all necessary steps to initialize a Python project:
    - Determine the virtual environment path based on project directory.
    - Create a virtual environment if it doesn't exist.
    - Install dependencies from requirements.txt (create empty if missing).
    - Create a pyproject.toml with dynamic metadata.
    - Install the project in editable mode.
    - Setup VSCode settings to point to the virtual environment interpreter.
    - Create a utils package directory.
    - Create a main.py file with boilerplate code.
    - Create a standard .gitignore file.
    - Generate a README.md file with usage instructions.

    Args:
        project_dir (str): The root directory of the Python project.

    Returns:
        None
    """
    # Get the virtual environment path for the project
    venv_path = get_venv_path(project_dir)

    # Create the virtual environment and upgrade pip
    create_virtualenv(venv_path)

    # Install dependencies from requirements.txt (or create an empty one)
    install_dependencies(venv_path, project_dir)

    # Create pyproject.toml with project metadata and build system config
    create_pyproject_toml(project_dir, venv_path)

    # Install the project in editable mode within the virtual environment
    install_editable_package(venv_path, project_dir)

    # Setup VSCode settings to use the virtual environment interpreter
    setup_vscode_settings(project_dir)

    # Create the utils directory as a Python package
    create_utils_module(project_dir)

    # Create the main.py boilerplate file
    create_main_file(project_dir)

    # Create a standard .gitignore file for Python projects
    create_gitignore(project_dir)

    # Create a README.md file with usage and setup instructions
    create_readme(project_dir)

    print(f"Project setup in {project_dir} is complete.")


if __name__ == "__main__":
    selected_dir = choose_directory()
    if selected_dir:
        setup_python_project(selected_dir)
    else:
        print("No directory selected. Exiting...")
