#!/usr/bin/env python3
"""
GitHub Repository Tool
A self-contained PySide6-based tool for creating and managing GitHub repositories.
No external CLI dependencies required - uses GitPython and GitHub API.
"""

import sys
import os
import git
import requests
import json
import webbrowser
from datetime import datetime
from typing import Optional, Dict, List

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QProgressBar, QMessageBox, QFileDialog, QTabWidget,
    QGroupBox, QGridLayout, QSplitter, QFrame, QMenuBar,
    QMenu, QStatusBar, QDialog, QFormLayout, QCheckBox, QInputDialog,
    QToolButton, QToolTip
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QPalette, QColor, QAction, QIcon

class GitWorker(QThread):
    """Background worker for Git operations using GitPython"""
    progress = Signal(str)
    finished = Signal(bool, str)
    
    def __init__(self, operation, folder, **kwargs):
        super().__init__()
        self.operation = operation
        self.folder = folder
        self.kwargs = kwargs
    
    def run(self):
        try:
            if self.operation == "init":
                self._init_git()
            elif self.operation == "add":
                self._add_files()
            elif self.operation == "commit":
                self._commit_changes()
            elif self.operation == "push":
                self._push_to_github()
            elif self.operation == "pull":
                self._pull_from_github()
            elif self.operation == "status":
                self._get_status()
        except Exception as e:
            self.finished.emit(False, str(e))
    
    def _init_git(self):
        self.progress.emit("Initializing Git repository...")
        repo = git.Repo.init(self.folder)
        self.finished.emit(True, "Git repository initialized successfully!")
    
    def _add_files(self):
        self.progress.emit("Adding files to staging...")
        repo = git.Repo(self.folder)
        repo.index.add("*")
        self.finished.emit(True, "Files added to staging!")
    
    def _commit_changes(self):
        commit_msg = self.kwargs.get("message", "Update")
        self.progress.emit(f"Committing changes: {commit_msg}")
        repo = git.Repo(self.folder)
        repo.index.commit(commit_msg)
        self.finished.emit(True, "Changes committed successfully!")
    
    def _push_to_github(self):
        self.progress.emit("Pushing to GitHub...")
        repo = git.Repo(self.folder)
        if repo.remotes:
            origin = repo.remote("origin")
            origin.push()
            self.finished.emit(True, "Successfully pushed to GitHub!")
        else:
            self.finished.emit(False, "No remote configured. Create a GitHub repository first.")
    
    def _pull_from_github(self):
        self.progress.emit("Pulling from GitHub...")
        repo = git.Repo(self.folder)
        if repo.remotes:
            origin = repo.remote("origin")
            origin.pull()
            self.finished.emit(True, "Successfully pulled from GitHub!")
        else:
            self.finished.emit(False, "No remote configured.")
    
    def _get_status(self):
        self.progress.emit("Getting Git status...")
        repo = git.Repo(self.folder)
        status_output = []
        status_output.append("=== Git Status ===")
        status_output.append(repo.git.status())
        self.finished.emit(True, "\n".join(status_output))

class GitHubTokenDialog(QDialog):
    """Dialog for GitHub token configuration with improved instructions"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GitHub Token Configuration")
        self.setModal(True)
        self.setGeometry(200, 200, 500, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("GitHub Personal Access Token")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "A GitHub Personal Access Token is required to create repositories.\n\n"
            "📋 How to get your token:\n"
            "1. Go to https://github.com/settings/tokens\n"
            "2. Click 'Generate new token (classic)'\n"
            "3. Give it a name (e.g., 'GitHub Repo Tool')\n"
            "4. Select 'repo' permissions\n"
            "5. Click 'Generate token'\n"
            "6. Copy the token (you won't see it again!)\n\n"
            "🔒 Your token is stored securely in this app only."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        layout.addWidget(instructions)
        
        # Token entry
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("GitHub Token:"))
        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.Password)
        self.token_edit.setPlaceholderText("Paste your GitHub token here...")
        token_layout.addWidget(self.token_edit)
        layout.addLayout(token_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Token")
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.help_btn = QPushButton("Open GitHub Tokens")
        self.help_btn.clicked.connect(self.open_github_tokens)
        button_layout.addWidget(self.help_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def open_github_tokens(self):
        """Open GitHub tokens page in browser"""
        webbrowser.open("https://github.com/settings/tokens")
    
    def get_token(self):
        return self.token_edit.text()

class GitHubRepoDialog(QDialog):
    """Dialog for GitHub repository creation"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create GitHub Repository")
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Repository name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Repository Name:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Visibility
        visibility_layout = QHBoxLayout()
        visibility_layout.addWidget(QLabel("Visibility:"))
        self.visibility_combo = QComboBox()
        self.visibility_combo.addItems(["Public", "Private"])
        visibility_layout.addWidget(self.visibility_combo)
        layout.addLayout(visibility_layout)
        
        # Description
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        desc_layout.addWidget(self.desc_edit)
        layout.addLayout(desc_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.create_btn = QPushButton("Create Repository")
        self.create_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.create_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_repo_info(self):
        return {
            "name": self.name_edit.text(),
            "visibility": self.visibility_combo.currentText().lower(),
            "description": self.desc_edit.toPlainText()
        }

class GitHubRepoTool(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.current_folder = ""
        self.git_repo = None
        self.github_token = None
        self.is_dark_mode = True
        self.setup_ui()
        self.setup_menu()
        self.apply_dark_theme()
    
    def setup_ui(self):
        self.setWindowTitle("GitHub Repository Tool")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Header with theme toggle
        header_layout = QHBoxLayout()
        title = QLabel("🚀 GitHub Repository Tool")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Theme toggle button
        self.theme_btn = QToolButton()
        self.theme_btn.setIcon(QIcon("🌙"))  # Moon for dark mode
        self.theme_btn.setToolTip("Toggle light/dark mode")
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.theme_btn.setStyleSheet("QToolButton { border: none; font-size: 16px; }")
        header_layout.addWidget(self.theme_btn)
        
        main_layout.addLayout(header_layout)
        
        # Folder selection
        folder_group = QGroupBox("📁 Project Folder")
        folder_layout = QHBoxLayout()
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("Select a project folder...")
        folder_layout.addWidget(self.folder_edit)
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_folder)
        self.browse_btn.setToolTip("Open folder browser to select your project directory")
        folder_layout.addWidget(self.browse_btn)
        
        folder_group.setLayout(folder_layout)
        main_layout.addWidget(folder_group)
        
        # GitHub token configuration
        token_group = QGroupBox("🔑 GitHub Configuration")
        token_layout = QHBoxLayout()
        self.token_status_label = QLabel("GitHub token not configured")
        token_layout.addWidget(self.token_status_label)
        
        self.configure_token_btn = QPushButton("Configure Token")
        self.configure_token_btn.clicked.connect(self.configure_github_token)
        self.configure_token_btn.setToolTip("Set up your GitHub Personal Access Token for creating repositories")
        token_layout.addWidget(self.configure_token_btn)
        
        token_group.setLayout(token_layout)
        main_layout.addWidget(token_group)
        
        # Git operations
        git_group = QGroupBox("🛠️ Git Operations")
        git_layout = QGridLayout()
        
        self.init_btn = QPushButton("Initialize Git")
        self.init_btn.clicked.connect(self.init_git)
        self.init_btn.setToolTip("Start tracking your project with Git (creates .git folder)")
        git_layout.addWidget(self.init_btn, 0, 0)
        
        self.add_btn = QPushButton("Add All Files")
        self.add_btn.clicked.connect(self.add_files)
        self.add_btn.setToolTip("Stage all files in your project for the next commit")
        git_layout.addWidget(self.add_btn, 0, 1)
        
        self.commit_btn = QPushButton("Commit Changes")
        self.commit_btn.clicked.connect(self.commit_changes)
        self.commit_btn.setToolTip("Save your changes with a message (like a checkpoint)")
        git_layout.addWidget(self.commit_btn, 0, 2)
        
        self.pull_btn = QPushButton("Pull from GitHub")
        self.pull_btn.clicked.connect(self.pull_from_github)
        self.pull_btn.setToolTip("Download latest changes from GitHub (if others made changes)")
        git_layout.addWidget(self.pull_btn, 1, 0)
        
        self.push_btn = QPushButton("Push to GitHub")
        self.push_btn.clicked.connect(self.push_to_github)
        self.push_btn.setToolTip("Upload your changes to GitHub")
        git_layout.addWidget(self.push_btn, 1, 1)
        
        self.status_btn = QPushButton("Git Status")
        self.status_btn.clicked.connect(self.show_git_status)
        self.status_btn.setToolTip("Show detailed information about your repository state")
        git_layout.addWidget(self.status_btn, 1, 2)
        
        git_group.setLayout(git_layout)
        main_layout.addWidget(git_group)
        
        # GitHub operations
        github_group = QGroupBox("🐙 GitHub Operations")
        github_layout = QHBoxLayout()
        
        self.create_repo_btn = QPushButton("Create GitHub Repository")
        self.create_repo_btn.clicked.connect(self.create_github_repo)
        self.create_repo_btn.setToolTip("Create a new repository on GitHub and upload your code")
        github_layout.addWidget(self.create_repo_btn)
        
        self.open_github_btn = QPushButton("Open in GitHub")
        self.open_github_btn.clicked.connect(self.open_in_github)
        self.open_github_btn.setToolTip("Open your repository in a web browser")
        github_layout.addWidget(self.open_github_btn)
        
        github_group.setLayout(github_layout)
        main_layout.addWidget(github_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Enhanced status display
        status_group = QGroupBox("📊 Project Status")
        status_layout = QVBoxLayout()
        
        # Summary status
        self.summary_label = QLabel("No project selected")
        self.summary_label.setStyleSheet("font-weight: bold; color: #666; padding: 5px;")
        status_layout.addWidget(self.summary_label)
        
        # Detailed status with better styling
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(150)
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 11px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        status_layout.addWidget(self.status_text)
        
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Select a folder to get started")
    
    def setup_menu(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        browse_action = QAction("Browse Folder", self)
        browse_action.setShortcut("Ctrl+O")
        browse_action.triggered.connect(self.browse_folder)
        file_menu.addAction(browse_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Git menu
        git_menu = menubar.addMenu("Git")
        
        init_action = QAction("Initialize Git", self)
        init_action.triggered.connect(self.init_git)
        git_menu.addAction(init_action)
        
        add_action = QAction("Add All Files", self)
        add_action.triggered.connect(self.add_files)
        git_menu.addAction(add_action)
        
        commit_action = QAction("Commit Changes", self)
        commit_action.triggered.connect(self.commit_changes)
        git_menu.addAction(commit_action)
        
        git_menu.addSeparator()
        
        pull_action = QAction("Pull from GitHub", self)
        pull_action.triggered.connect(self.pull_from_github)
        git_menu.addAction(pull_action)
        
        push_action = QAction("Push to GitHub", self)
        push_action.triggered.connect(self.push_to_github)
        git_menu.addAction(push_action)
        
        # GitHub menu
        github_menu = menubar.addMenu("GitHub")
        
        token_action = QAction("Configure Token", self)
        token_action.triggered.connect(self.configure_github_token)
        github_menu.addAction(token_action)
        
        github_menu.addSeparator()
        
        create_repo_action = QAction("Create Repository", self)
        create_repo_action.triggered.connect(self.create_github_repo)
        github_menu.addAction(create_repo_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.theme_btn.setIcon(QIcon("🌙"))
            self.apply_dark_theme()
        else:
            self.theme_btn.setIcon(QIcon("☀️"))
            self.apply_light_theme()
    
    def apply_dark_theme(self):
        """Apply a professional dark theme"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        self.setPalette(palette)
    
    def apply_light_theme(self):
        """Apply a clean light theme"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(0, 0, 255))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        self.setPalette(palette)
    
    def configure_github_token(self):
        """Configure GitHub token"""
        dialog = GitHubTokenDialog(self)
        if dialog.exec() == QDialog.Accepted:
            token = dialog.get_token()
            if token:
                # Test the token
                headers = {"Authorization": f"token {token}"}
                try:
                    response = requests.get("https://api.github.com/user", headers=headers)
                    if response.status_code == 200:
                        user_data = response.json()
                        self.github_token = token
                        self.token_status_label.setText(f"✅ Token configured for: {user_data['login']}")
                        QMessageBox.information(self, "Success", f"GitHub token configured successfully!\nAuthenticated as: {user_data['login']}")
                    else:
                        QMessageBox.critical(self, "Error", "Invalid GitHub token. Please check your token and try again.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to validate token: {str(e)}")
    
    def browse_folder(self):
        """Open folder browser dialog"""
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder:
            self.current_folder = folder
            self.folder_edit.setText(folder)
            self.update_status()
    
    def update_status(self):
        """Update the status display with better summarization"""
        if not self.current_folder:
            self.summary_label.setText("No project selected")
            self.status_text.setText("Select a folder to see project status")
            return
        
        try:
            self.git_repo = git.Repo(self.current_folder)
            status = self.get_git_status()
            summary = self.get_status_summary()
            self.summary_label.setText(summary)
            self.status_text.setText(status)
        except git.exc.InvalidGitRepositoryError:
            self.summary_label.setText("📁 Not a Git repository")
            self.status_text.setText("This folder is not tracked by Git.\n\nClick 'Initialize Git' to start tracking your project.")
        except Exception as e:
            self.summary_label.setText("❌ Error")
            self.status_text.setText(f"Error reading project: {str(e)}")
    
    def get_status_summary(self):
        """Get a user-friendly status summary"""
        if not self.git_repo:
            return "No repository"
        
        try:
            # Basic info
            branch = self.git_repo.active_branch.name
            has_remote = bool(self.git_repo.remotes)
            
            # Status indicators
            is_dirty = self.git_repo.is_dirty()
            modified_count = len([item.a_path for item in self.git_repo.index.diff(None)])
            untracked_count = len(self.git_repo.untracked_files)
            
            # Build summary
            summary_parts = []
            summary_parts.append(f"🌿 Branch: {branch}")
            
            if has_remote:
                summary_parts.append("🌐 Connected to GitHub")
            else:
                summary_parts.append("🌐 No GitHub connection")
            
            if is_dirty:
                if modified_count > 0:
                    summary_parts.append(f"📝 {modified_count} modified files")
                if untracked_count > 0:
                    summary_parts.append(f"🆕 {untracked_count} new files")
            else:
                summary_parts.append("✅ All changes saved")
            
            return " | ".join(summary_parts)
            
        except Exception:
            return "Status unknown"
    
    def get_git_status(self):
        """Get detailed Git status with better formatting"""
        if not self.git_repo:
            return "No repository"
        
        status_lines = []
        status_lines.append("=== Git Repository Status ===")
        
        try:
            # Branch info
            branch = self.git_repo.active_branch.name
            status_lines.append(f"Branch: {branch}")
            
            # Remote info
            if self.git_repo.remotes:
                remote_url = next(self.git_repo.remote().urls)
                status_lines.append(f"Remote: {remote_url}")
            else:
                status_lines.append("Remote: None configured")
            
            # Working directory status
            if self.git_repo.is_dirty():
                status_lines.append("Status: Working directory has uncommitted changes")
                
                # Show modified files
                modified_files = [item.a_path for item in self.git_repo.index.diff(None)]
                if modified_files:
                    status_lines.append(f"Modified files: {len(modified_files)}")
                
                # Show untracked files
                untracked_files = self.git_repo.untracked_files
                if untracked_files:
                    status_lines.append(f"Untracked files: {len(untracked_files)}")
            else:
                status_lines.append("Status: Working directory is clean")
            
            # Last commit
            try:
                last_commit = self.git_repo.head.commit
                commit_date = datetime.fromtimestamp(last_commit.committed_date)
                status_lines.append(f"Last commit: {commit_date.strftime('%Y-%m-%d %H:%M:%S')}")
                status_lines.append(f"Message: {last_commit.message.strip()}")
            except Exception:
                status_lines.append("Last commit: None")
        
        except Exception as e:
            status_lines.append(f"Error getting status: {str(e)}")
        
        return "\n".join(status_lines)
    
    def init_git(self):
        """Initialize Git repository"""
        if not self.current_folder:
            QMessageBox.warning(self, "Warning", "Please select a folder first.")
            return
        
        self.worker = GitWorker("init", self.current_folder)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_git_operation_finished)
        self.start_progress()
        self.worker.start()
    
    def add_files(self):
        """Add all files to staging"""
        if not self.current_folder:
            QMessageBox.warning(self, "Warning", "Please select a folder first.")
            return
        
        self.worker = GitWorker("add", self.current_folder)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_git_operation_finished)
        self.start_progress()
        self.worker.start()
    
    def commit_changes(self):
        """Commit staged changes"""
        if not self.current_folder:
            QMessageBox.warning(self, "Warning", "Please select a folder first.")
            return
        
        commit_msg, ok = QInputDialog.getText(self, "Commit Message", "Enter commit message:")
        if ok and commit_msg:
            self.worker = GitWorker("commit", self.current_folder, message=commit_msg)
            self.worker.progress.connect(self.update_progress)
            self.worker.finished.connect(self.on_git_operation_finished)
            self.start_progress()
            self.worker.start()
    
    def push_to_github(self):
        """Push changes to GitHub"""
        if not self.current_folder:
            QMessageBox.warning(self, "Warning", "Please select a folder first.")
            return
        
        self.worker = GitWorker("push", self.current_folder)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_git_operation_finished)
        self.start_progress()
        self.worker.start()
    
    def pull_from_github(self):
        """Pull changes from GitHub"""
        if not self.current_folder:
            QMessageBox.warning(self, "Warning", "Please select a folder first.")
            return
        
        self.worker = GitWorker("pull", self.current_folder)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_git_operation_finished)
        self.start_progress()
        self.worker.start()
    
    def show_git_status(self):
        """Show detailed Git status"""
        if not self.current_folder:
            QMessageBox.warning(self, "Warning", "Please select a folder first.")
            return
        
        self.worker = GitWorker("status", self.current_folder)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_git_status_finished)
        self.start_progress()
        self.worker.start()
    
    def create_github_repo(self):
        """Create GitHub repository"""
        if not self.current_folder:
            QMessageBox.warning(self, "Warning", "Please select a folder first.")
            return
        
        if not self.github_token:
            QMessageBox.warning(self, "Warning", "Please configure GitHub token first.")
            self.configure_github_token()
            return
        
        dialog = GitHubRepoDialog(self)
        if dialog.exec() == QDialog.Accepted:
            repo_info = dialog.get_repo_info()
            self.create_github_repository(repo_info)
    
    def create_github_repository(self, repo_info):
        """Create GitHub repository using GitHub API"""
        try:
            # Ensure Git is initialized
            if not os.path.exists(os.path.join(self.current_folder, ".git")):
                repo = git.Repo.init(self.current_folder)
            else:
                repo = git.Repo(self.current_folder)
            
            # Add and commit files
            repo.index.add("*")
            try:
                repo.index.commit("Initial commit")
            except git.exc.GitCommandError:
                pass  # No changes to commit
            
            # Create GitHub repository using API
            repo_name = repo_info["name"] or os.path.basename(self.current_folder)
            
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            data = {
                "name": repo_name,
                "private": repo_info["visibility"] == "private",
                "description": repo_info["description"] or ""
            }
            
            response = requests.post(
                "https://api.github.com/user/repos",
                json=data,
                headers=headers
            )
            
            if response.status_code == 201:
                repo_data = response.json()
                repo_url = repo_data["html_url"]
                clone_url = repo_data["clone_url"]
                
                # Add remote and push
                if not repo.remotes:
                    origin = repo.create_remote("origin", clone_url)
                else:
                    origin = repo.remote("origin")
                    origin.set_url(clone_url)
                
                origin.push()
                
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Repository created successfully!\n\n"
                    f"Name: {repo_name}\n"
                    f"URL: {repo_url}\n"
                    f"Code pushed to GitHub."
                )
            else:
                error_msg = response.json().get("message", "Unknown error")
                QMessageBox.critical(self, "Error", f"Failed to create repository: {error_msg}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
    
    def open_in_github(self):
        """Open repository in GitHub"""
        if not self.current_folder:
            QMessageBox.warning(self, "Warning", "Please select a folder first.")
            return
        
        try:
            repo = git.Repo(self.current_folder)
            if repo.remotes:
                remote_url = next(repo.remote().urls)
                if 'github.com' in remote_url:
                    # Convert SSH to HTTPS if needed
                    if remote_url.startswith('git@'):
                        remote_url = remote_url.replace('git@github.com:', 'https://github.com/').replace('.git', '')
                    else:
                        remote_url = remote_url.replace('.git', '')
                    
                    webbrowser.open(remote_url)
                else:
                    QMessageBox.information(self, "Info", "No GitHub remote found for this repository.")
            else:
                QMessageBox.information(self, "Info", "No remote configured for this repository.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open GitHub: {str(e)}")
    
    def start_progress(self):
        """Start progress bar"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
    
    def update_progress(self, message):
        """Update progress message"""
        self.status_bar.showMessage(message)
    
    def on_git_operation_finished(self, success, message):
        """Handle Git operation completion"""
        self.progress_bar.setVisible(False)
        if success:
            QMessageBox.information(self, "Success", message)
            self.update_status()
        else:
            QMessageBox.critical(self, "Error", message)
        self.status_bar.showMessage("Ready")
    
    def on_git_status_finished(self, success, status_output):
        """Handle Git status completion"""
        self.progress_bar.setVisible(False)
        if success:
            # Show status in a new dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Git Status")
            dialog.setGeometry(200, 200, 600, 400)
            
            layout = QVBoxLayout(dialog)
            text_edit = QTextEdit()
            text_edit.setPlainText(status_output)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.exec()
        else:
            QMessageBox.critical(self, "Error", status_output)
        self.status_bar.showMessage("Ready")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """GitHub Repository Tool v2.1

A self-contained PySide6-based tool for creating and managing GitHub repositories.

Features:
• Initialize Git repositories
• Add and commit files
• Push/pull from GitHub
• Create GitHub repositories via API
• View detailed Git status
• Professional dark/light theme interface
• No external CLI dependencies required
• User-friendly interface with tooltips

Requirements:
• Python with GitPython and requests libraries
• GitHub Personal Access Token

Keyboard shortcuts:
• Ctrl+O: Browse folder
• Ctrl+Q: Quit"""
        
        QMessageBox.about(self, "About", about_text)

def main():
    """Main entry point"""
    # Launch GUI
    app = QApplication(sys.argv)
    app.setApplicationName("GitHub Repository Tool")
    
    window = GitHubRepoTool()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    sys.exit(main()) 