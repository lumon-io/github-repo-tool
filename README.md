# GitHub Repository Setup Tool

A polished Python tool to easily create and manage GitHub repositories from local folders. Works both as a GUI application and command-line tool.

## Features

- **Dual Mode**: GUI interface or command-line operation
- **Mac-Style Design**: Beautiful, modern interface with Apple-inspired colors and typography
- **Comprehensive Git Management**: Full Git workflow with status, pull, push, commit
- **Git Credential Management**: Configure username and email via UI
- **GitHub Token Management**: Configure GitHub Personal Access Token for API access
- **Smart Repository Setup**: Automatically initializes Git repositories when needed
- **GitHub Integration**: Creates repositories and pushes code in one step
- **Detailed GitHub Data**: View repository stats, commits, pull requests, and issues
- **Repository Options**: Choose between public/private repositories with descriptions
- **Real-time Status**: Detailed repository and file status with visual indicators
- **File Management**: View modified, untracked, and staged files
- **Easy Termination**: Multiple ways to exit the program (Ctrl+Q, Esc, menu)
- **Progress Feedback**: Visual progress indicators and detailed status updates
- **Quick Actions**: Open folders in explorer, open repositories in GitHub

## Requirements

- Python 3.6+
- Git installed and configured
- GitHub CLI (gh) installed and authenticated

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install GitHub CLI:
   - **Windows**: Download from https://cli.github.com/
   - **macOS**: `brew install gh`
   - **Linux**: Follow instructions at https://cli.github.com/

3. Authenticate with GitHub:
```bash
gh auth login
```

4. Install optional dependencies:
```bash
pip install pillow questionary InquirerPy textual
```

## Usage

### Interactive Mode Selection

When you run the program without arguments, it will detect your environment and ask you to choose:

```bash
python github_repo_tool.py
```

**Example Output:**
```
    /\\
   /  \\
  /____\\
  |    |
  |NASA|
  |    |
 /|    |\\
/_|____|_\\

🚀 GitHub Repository Setup Tool
========================================
Choose your preferred mode:
1. GUI Mode - Beautiful graphical interface
2. CLI Mode - Command line interface
3. Exit

Enter your choice (1-3): 
```

### GUI Mode

Run the program without arguments to launch the GUI:

```bash
python github_repo_tool.py
```

**GUI Features:**
- **Beautiful Mac-Style Interface**: Apple-inspired design with modern colors and typography
- Browse and select project folders
- Choose repository visibility (Public/Private)
- Add repository descriptions
- **Git Credential Management**: Configure username and email through UI
- **GitHub Token Management**: Configure Personal Access Token for API access
- **Complete Git Workflow**: Initialize, status, add, commit, pull, push
- **Real-time Status**: Shows repository info, branch, remote, commits ahead/behind
- **File Status Panel**: Displays modified, untracked, and staged files
- **Git Status Window**: Detailed git status in separate window
- **GitHub Details Window**: View repository stats, commits, pull requests, issues
- Create and push to GitHub
- Open folders in file explorer
- Open repositories in GitHub

**Keyboard Shortcuts:**
- `Ctrl+O`: Browse folder
- `Ctrl+Q`: Quit
- `Esc`: Quit

### Command Line Mode

Use the program directly from the command line:

```bash
# Basic usage - create public repository
python github_repo_tool.py /path/to/your/project

# Create private repository
python github_repo_tool.py /path/to/your/project --private

# Add description
python github_repo_tool.py /path/to/your/project --description "My awesome project"

# Create without pushing (just create the repo)
python github_repo_tool.py /path/to/your/project --no-push

# Force GUI mode even with folder argument
python github_repo_tool.py /path/to/your/project --gui

# Force CLI mode
python github_repo_tool.py --cli /path/to/your/project
```

### Command Line Options

- `folder`: Path to the project folder (optional for GUI mode)
- `--private`: Create private repository (default: public)
- `--description, -d`: Repository description
- `--no-push`: Don't push code after creation
- `--gui`: Force GUI mode
- `--cli`: Force CLI mode

## Examples

### Quick Setup
```bash
# Navigate to your project folder
cd /path/to/my-project

# Interactive mode - choose GUI or CLI
python github_repo_tool.py

# Or force CLI mode
python github_repo_tool.py .

# Or force GUI mode
python github_repo_tool.py --gui
```

### Advanced Usage
```bash
# Create a private repository with description
python github_repo_tool.py ./my-secret-project --private --description "Internal tools and scripts"

# Create repository without pushing (useful for existing repos)
python github_repo_tool.py ./existing-project --no-push
```

## Program Flow

1. **Folder Selection**: Choose a project folder (GUI) or specify path (CLI)
2. **Git Check**: Program checks if folder is a Git repository
3. **Git Initialization**: If needed, initializes Git repository
4. **File Staging**: Adds all files to Git
5. **Commit**: Creates initial commit
6. **GitHub Creation**: Creates repository on GitHub
7. **Push**: Pushes code to GitHub repository

## Error Handling

The program includes comprehensive error handling for:
- Missing Git installation
- Missing GitHub CLI
- Invalid folder paths
- Network connectivity issues
- Authentication problems
- Repository creation failures

## Troubleshooting

### Common Issues

1. **"Git is not installed"**
   - Install Git from https://git-scm.com/

2. **"GitHub CLI not found"**
   - Install GitHub CLI from https://cli.github.com/
   - Run `gh auth login` to authenticate

3. **"Authentication failed"**
   - Run `gh auth login` and follow the prompts
   - Ensure you have proper GitHub permissions

4. **"Repository already exists"**
   - The repository name conflicts with an existing one
   - Rename your folder or use a different name

### Getting Help

- Use `--help` for command-line options
- Check the "About" dialog in GUI mode
- Ensure all dependencies are properly installed

## Development

The program is structured as a class-based application with:
- `GitHubRepoSetup`: Main GUI class
- `run_command_line()`: Command-line functionality
- `main()`: Entry point with argument parsing

## License

This tool is provided as-is for educational and development purposes. 