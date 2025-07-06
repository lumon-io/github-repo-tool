#!/usr/bin/env python3
"""
GitHub Repository Tool
A modern PySide6-based tool for creating and managing GitHub repositories.
"""

import sys
import os
import subprocess
import git
import requests
import json
from datetime import datetime
from typing import Optional, Dict, List

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QProgressBar, QMessageBox, QFileDialog, QTabWidget,
    QGroupBox, QGridLayout, QSplitter, QFrame, QMenuBar,
    QMenu, QStatusBar, QDialog, QFormLayout, QCheckBox, QInputDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QPalette, QColor, QAction, QIcon

class GitWorker(QThread):
    """Background worker for Git operations"""
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
        os.chdir(self.folder)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        self.finished.emit(True, "Git repository initialized successfully!")
    
    def _add_files(self):
        self.progress.emit("Adding files to staging...")
        os.chdir(self.folder)
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        self.finished.emit(True, "Files added to staging!")
    
    def _commit_changes(self):
        commit_msg = self.kwargs.get("message", "Update")
        self.progress.emit(f"Committing changes: {commit_msg}")
        os.chdir(self.folder)
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
        self.finished.emit(True, "Changes committed successfully!")
    
    def _push_to_github(self):
        self.progress.emit("Pushing to GitHub...")
        os.chdir(self.folder)
        subprocess.run(["git", "push"], check=True, capture_output=True)
        self.finished.emit(True, "Successfully pushed to GitHub!")
    
    def _pull_from_github(self):
        self.progress.emit("Pulling from GitHub...")
        os.chdir(self.folder)
        subprocess.run(["git", "pull"], check=True, capture_output=True)
        self.finished.emit(True, "Successfully pulled from GitHub!")
    
    def _get_status(self):
        self.progress.emit("Getting Git status...")
        os.chdir(self.folder)
        result = subprocess.run(["git", "status"], capture_output=True, text=True, check=True)
        self.finished.emit(True, result.stdout)

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
        
        # Folder selection
        folder_group = QGroupBox("Project Folder")
        folder_layout = QHBoxLayout()
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("Select a project folder...")
        folder_layout.addWidget(self.folder_edit)
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.browse_btn)
        
        folder_group.setLayout(folder_layout)
        main_layout.addWidget(folder_group)
        
        # Git operations
        git_group = QGroupBox("Git Operations")
        git_layout = QGridLayout()
        
        self.init_btn = QPushButton("Initialize Git")
        self.init_btn.clicked.connect(self.init_git)
        git_layout.addWidget(self.init_btn, 0, 0)
        
        self.add_btn = QPushButton("Add All Files")
        self.add_btn.clicked.connect(self.add_files)
        git_layout.addWidget(self.add_btn, 0, 1)
        
        self.commit_btn = QPushButton("Commit Changes")
        self.commit_btn.clicked.connect(self.commit_changes)
        git_layout.addWidget(self.commit_btn, 0, 2)
        
        self.pull_btn = QPushButton("Pull from GitHub")
        self.pull_btn.clicked.connect(self.pull_from_github)
        git_layout.addWidget(self.pull_btn, 1, 0)
        
        self.push_btn = QPushButton("Push to GitHub")
        self.push_btn.clicked.connect(self.push_to_github)
        git_layout.addWidget(self.push_btn, 1, 1)
        
        self.status_btn = QPushButton("Git Status")
        self.status_btn.clicked.connect(self.show_git_status)
        git_layout.addWidget(self.status_btn, 1, 2)
        
        git_group.setLayout(git_layout)
        main_layout.addWidget(git_group)
        
        # GitHub operations
        github_group = QGroupBox("GitHub Operations")
        github_layout = QHBoxLayout()
        
        self.create_repo_btn = QPushButton("Create GitHub Repository")
        self.create_repo_btn.clicked.connect(self.create_github_repo)
        github_layout.addWidget(self.create_repo_btn)
        
        self.open_github_btn = QPushButton("Open in GitHub")
        self.open_github_btn.clicked.connect(self.open_in_github)
        github_layout.addWidget(self.open_github_btn)
        
        github_group.setLayout(github_layout)
        main_layout.addWidget(github_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Status display
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(200)
        self.status_text.setReadOnly(True)
        main_layout.addWidget(self.status_text)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
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
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
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
    
    def browse_folder(self):
        """Open folder browser dialog"""
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder:
            self.current_folder = folder
            self.folder_edit.setText(folder)
            self.update_status()
    
    def update_status(self):
        """Update the status display"""
        if not self.current_folder:
            self.status_text.setText("No folder selected")
            return
        
        try:
            self.git_repo = git.Repo(self.current_folder)
            status = self.get_git_status()
            self.status_text.setText(status)
        except git.exc.InvalidGitRepositoryError:
            self.status_text.setText("Not a Git repository. Click 'Initialize Git' to start.")
        except Exception as e:
            self.status_text.setText(f"Error: {str(e)}")
    
    def get_git_status(self):
        """Get detailed Git status"""
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
        
        dialog = GitHubRepoDialog(self)
        if dialog.exec() == QDialog.Accepted:
            repo_info = dialog.get_repo_info()
            self.create_github_repository(repo_info)
    
    def create_github_repository(self, repo_info):
        """Create GitHub repository using GitHub CLI"""
        try:
            os.chdir(self.current_folder)
            
            # Ensure Git is initialized
            if not os.path.exists(".git"):
                subprocess.run(["git", "init"], check=True, capture_output=True)
            
            # Add and commit files
            subprocess.run(["git", "add", "."], check=True, capture_output=True)
            try:
                subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                pass  # No changes to commit
            
            # Create GitHub repository
            repo_name = repo_info["name"] or os.path.basename(self.current_folder)
            visibility = "--private" if repo_info["visibility"] == "private" else "--public"
            
            cmd = ["gh", "repo", "create", repo_name, "--source=.", visibility, "--push"]
            if repo_info["description"]:
                cmd.extend(["--description", repo_info["description"]])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            QMessageBox.information(self, "Success", f"Repository created successfully!\n{result.stdout}")
            
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"Failed to create repository: {e.stderr}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
    
    def open_in_github(self):
        """Open repository in GitHub"""
        if not self.current_folder:
            QMessageBox.warning(self, "Warning", "Please select a folder first.")
            return
        
        try:
            repo = git.Repo(self.current_folder)
            remote_url = next(repo.remote().urls)
            if 'github.com' in remote_url:
                # Convert SSH to HTTPS if needed
                if remote_url.startswith('git@'):
                    remote_url = remote_url.replace('git@github.com:', 'https://github.com/').replace('.git', '')
                else:
                    remote_url = remote_url.replace('.git', '')
                
                import webbrowser
                webbrowser.open(remote_url)
            else:
                QMessageBox.information(self, "Info", "No GitHub remote found for this repository.")
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
        about_text = """GitHub Repository Tool v1.0

A professional PySide6-based tool for creating and managing GitHub repositories.

Features:
• Initialize Git repositories
• Add and commit files
• Push/pull from GitHub
• Create GitHub repositories
• View detailed Git status
• Professional dark theme interface

Requirements:
• Git installed and configured
• GitHub CLI (gh) installed and authenticated

Keyboard shortcuts:
• Ctrl+O: Browse folder
• Ctrl+Q: Quit"""
        
        QMessageBox.about(self, "About", about_text)

def main():
    """Main entry point"""
    # Check dependencies
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: Git is not installed or not in PATH")
        return 1
    
    try:
        subprocess.run(["gh", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: GitHub CLI (gh) is not installed or not in PATH")
        print("Install from: https://cli.github.com/")
        return 1
    
    # Launch GUI
    app = QApplication(sys.argv)
    app.setApplicationName("GitHub Repository Tool")
    
    window = GitHubRepoTool()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    sys.exit(main()) 