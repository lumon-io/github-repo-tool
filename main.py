"""
GitHub Repository Setup Tool (PySide6 Edition)

Instructions:
- Install dependencies:
    pip install PySide6 qtawesome gitpython requests
- Run the app:
    python main.py

Features:
- Modern dashboard UI (light/dark mode)
- All Git/GitHub management (init, status, add, commit, push, pull, create repo, credentials, token)
- Human-readable, color-coded log panel (clickable links, export)
- Responsive, beautiful, and user-friendly
"""

import sys
import os
import subprocess
import git
import requests
import threading
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QTextEdit, QFrame, QFileDialog,
    QTabWidget, QCheckBox, QMessageBox, QSplitter, QMenuBar, QMenu, QInputDialog
)
from PySide6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor, QIcon, QAction
from PySide6.QtCore import Qt
try:
    import qtawesome as qta
    ICONS = True
except ImportError:
    ICONS = False

APP_TITLE = "GitHub Repository Setup Tool"

class LogPanel(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 11))
        self.setMinimumHeight(120)
    def log(self, message, level='info'):
        color = {'info': '#222', 'success': '#34c759', 'error': '#ff3b30', 'warning': '#ff9500'}.get(level, '#222')
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(message + '\n', fmt)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
    def export_log(self, path):
        with open(path, 'w') as f:
            f.write(self.toPlainText())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1000, 750)
        self.setStyleSheet(self.light_stylesheet())
        self.dark_mode = False
        self.github_token = None
        self.git_username = None
        self.git_email = None
        self.setup_ui()

    def setup_ui(self):
        # Menu bar
        menubar = QMenuBar()
        file_menu = QMenu("File", self)
        export_log_action = QAction("Export Log", self)
        export_log_action.triggered.connect(self.export_log)
        file_menu.addAction(export_log_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        menubar.addMenu(file_menu)
        view_menu = QMenu("View", self)
        self.dark_mode_action = QAction("Toggle Dark Mode", self)
        self.dark_mode_action.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(self.dark_mode_action)
        menubar.addMenu(view_menu)
        self.setMenuBar(menubar)

        # Main layout
        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setSpacing(18)

        # Title
        title = QLabel(f"🚀 {APP_TITLE}")
        title.setObjectName("title")
        subtitle = QLabel("Manage your Git repositories with style")
        subtitle.setObjectName("subtitle")
        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # Project Folder Card
        folder_card = QFrame()
        folder_card.setObjectName("card")
        folder_layout = QHBoxLayout(folder_card)
        folder_label = QLabel("Project Folder:")
        self.folder_input = QLineEdit()
        browse_btn = QPushButton("Browse")
        if ICONS:
            browse_btn.setIcon(self.icon("folder-open"))
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(browse_btn)
        main_layout.addWidget(folder_card)

        # Repo Options Card
        options_card = QFrame()
        options_card.setObjectName("card")
        options_layout = QHBoxLayout(options_card)
        visibility_label = QLabel("Visibility:")
        self.visibility_combo = QComboBox()
        self.visibility_combo.addItems(["Public", "Private"])
        desc_label = QLabel("Description:")
        self.desc_input = QLineEdit()
        options_layout.addWidget(visibility_label)
        options_layout.addWidget(self.visibility_combo)
        options_layout.addWidget(desc_label)
        options_layout.addWidget(self.desc_input)
        main_layout.addWidget(options_card)

        # Credentials Card
        cred_card = QFrame()
        cred_card.setObjectName("card")
        cred_layout = QHBoxLayout(cred_card)
        cred_btn = QPushButton("Configure Git Credentials")
        cred_btn.clicked.connect(self.configure_git_credentials)
        token_btn = QPushButton("Configure GitHub Token")
        token_btn.clicked.connect(self.configure_github_token)
        cred_layout.addWidget(cred_btn)
        cred_layout.addWidget(token_btn)
        main_layout.addWidget(cred_card)

        # Git Management Card
        git_card = QFrame()
        git_card.setObjectName("card")
        git_layout = QGridLayout(git_card)
        self.init_btn = QPushButton("Initialize Git")
        self.init_btn.clicked.connect(self.init_git)
        self.status_btn = QPushButton("Git Status")
        self.status_btn.clicked.connect(self.git_status)
        self.add_btn = QPushButton("Add All Files")
        self.add_btn.clicked.connect(self.git_add_all)
        self.commit_btn = QPushButton("Commit Changes")
        self.commit_btn.clicked.connect(self.git_commit)
        self.pull_btn = QPushButton("Pull from Remote")
        self.pull_btn.clicked.connect(self.git_pull)
        self.push_btn = QPushButton("Push to Remote")
        self.push_btn.clicked.connect(self.git_push)
        self.create_btn = QPushButton("Create & Push to GitHub")
        self.create_btn.clicked.connect(self.create_or_push_repo)
        git_layout.addWidget(self.init_btn, 0, 0)
        git_layout.addWidget(self.status_btn, 0, 1)
        git_layout.addWidget(self.add_btn, 0, 2)
        git_layout.addWidget(self.commit_btn, 0, 3)
        git_layout.addWidget(self.pull_btn, 1, 0)
        git_layout.addWidget(self.push_btn, 1, 1)
        git_layout.addWidget(self.create_btn, 1, 2)
        main_layout.addWidget(git_card)

        # Status/Log Splitter
        splitter = QSplitter(Qt.Vertical)
        # Status Panel
        status_panel = QFrame()
        status_panel.setObjectName("card")
        status_layout = QVBoxLayout(status_panel)
        status_label = QLabel("Repository Status")
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_text)
        splitter.addWidget(status_panel)
        # Log Panel
        self.log_panel = LogPanel()
        splitter.addWidget(self.log_panel)
        splitter.setSizes([300, 200])
        main_layout.addWidget(splitter)

        self.setCentralWidget(main)

    def icon(self, name):
        if ICONS:
            return qta.icon(f"fa5s.{name}")
        return None

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.setStyleSheet(self.dark_stylesheet() if self.dark_mode else self.light_stylesheet())

    def light_stylesheet(self):
        return """
        QMainWindow { background: #f5f5f7; }
        #card { background: #fff; border-radius: 12px; padding: 18px; }
        QLabel#title { font-size: 28px; font-weight: bold; }
        QLabel#subtitle { color: #888; font-size: 16px; }
        QPushButton { background: #007aff; color: white; border-radius: 8px; padding: 8px 20px; }
        QPushButton#success { background: #34c759; }
        QPushButton#danger { background: #ff3b30; }
        QLineEdit, QComboBox, QTextEdit { border-radius: 6px; border: 1px solid #ccc; padding: 6px; }
        QSplitter::handle { background: #e0e0e0; }
        """

    def dark_stylesheet(self):
        return """
        QMainWindow { background: #23272e; }
        #card { background: #2c2f36; border-radius: 12px; padding: 18px; }
        QLabel#title { font-size: 28px; font-weight: bold; color: #fff; }
        QLabel#subtitle { color: #aaa; font-size: 16px; }
        QPushButton { background: #007aff; color: white; border-radius: 8px; padding: 8px 20px; }
        QPushButton#success { background: #34c759; }
        QPushButton#danger { background: #ff3b30; }
        QLineEdit, QComboBox, QTextEdit { border-radius: 6px; border: 1px solid #444; background: #23272e; color: #fff; padding: 6px; }
        QSplitter::handle { background: #444; }
        """

    def log(self, message, level='info'):
        self.log_panel.log(message, level)

    def export_log(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Log", "log.txt", "Text Files (*.txt)")
        if path:
            self.log_panel.export_log(path)
            self.log(f"Log exported to {path}", 'success')

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder:
            self.folder_input.setText(folder)
            self.log(f"Selected folder: {folder}", 'info')

    # --- Git/GitHub logic below ---
    def get_folder(self):
        folder = self.folder_input.text().strip()
        if not folder or not os.path.isdir(folder):
            self.log("No valid folder selected.", 'error')
            return None
        return folder

    def init_git(self):
        folder = self.get_folder()
        if not folder:
            return
        try:
            subprocess.run(["git", "init"], cwd=folder, check=True, capture_output=True)
            self.log("✅ Git repository initialized!", 'success')
        except subprocess.CalledProcessError as e:
            self.log(f"Error initializing git: {e.stderr.decode().strip()}", 'error')

    def git_status(self):
        folder = self.get_folder()
        if not folder:
            return
        try:
            result = subprocess.run(["git", "status"], cwd=folder, check=True, capture_output=True, text=True)
            self.status_text.setPlainText(result.stdout)
            self.log(result.stdout, 'info')
        except subprocess.CalledProcessError as e:
            self.log(f"Error getting status: {e.stderr}", 'error')

    def git_add_all(self):
        folder = self.get_folder()
        if not folder:
            return
        try:
            subprocess.run(["git", "add", "."], cwd=folder, check=True, capture_output=True)
            self.log("✅ All files added to staging!", 'success')
        except subprocess.CalledProcessError as e:
            self.log(f"Error adding files: {e.stderr}", 'error')

    def git_commit(self):
        folder = self.get_folder()
        if not folder:
            return
        msg, ok = self.get_text_dialog("Commit Message", "Enter commit message:")
        if not ok or not msg:
            self.log("Commit cancelled.", 'warning')
            return
        try:
            subprocess.run(["git", "commit", "-m", msg], cwd=folder, check=True, capture_output=True)
            self.log("✅ Changes committed!", 'success')
        except subprocess.CalledProcessError as e:
            self.log(f"Error committing: {e.stderr}", 'error')

    def git_pull(self):
        folder = self.get_folder()
        if not folder:
            return
        try:
            result = subprocess.run(["git", "pull"], cwd=folder, check=True, capture_output=True, text=True)
            self.log(f"✅ Pull successful!\n{result.stdout}", 'success')
        except subprocess.CalledProcessError as e:
            self.log(f"Pull failed: {e.stderr}", 'error')

    def git_push(self):
        folder = self.get_folder()
        if not folder:
            return
        try:
            result = subprocess.run(["git", "push"], cwd=folder, check=True, capture_output=True, text=True)
            self.log(f"✅ Push successful!\n{result.stdout}", 'success')
        except subprocess.CalledProcessError as e:
            self.log(f"Push failed: {e.stderr}", 'error')

    def create_or_push_repo(self):
        """Create GitHub repository and push code"""
        folder = self.folder_input.text().strip()
        if not folder or not os.path.isdir(folder):
            self.log("⚠️ Please select a valid folder.", 'error')
            return
        
        def run_operation():
            try:
                self.log("🚀 Starting GitHub repository creation...", 'info')
                os.chdir(folder)
                
                # Initialize Git if needed
                try:
                    repo = git.Repo('.')
                    self.log("✅ Git repository found", 'success')
                except git.exc.InvalidGitRepositoryError:
                    self.log("📁 Initializing Git repository...", 'info')
                    subprocess.run(["git", "init"], check=True, capture_output=True)
                    repo = git.Repo('.')
                    self.log("✅ Git repository initialized", 'success')
                
                # Add and commit files
                repo.git.add(A=True)
                try:
                    commit_message = "Initial commit"
                    repo.index.commit(commit_message)
                    self.log("✅ Files committed", 'success')
                except git.exc.GitCommandError:
                    self.log("ℹ️ No changes to commit", 'info')
                
                # Create GitHub repository
                repo_name = os.path.basename(folder)
                self.log(f"🐙 Creating GitHub repository '{repo_name}'...", 'info')
                
                visibility = "--public" if self.visibility_combo.currentText() == "Public" else "--private"
                description = self.desc_input.text().strip()
                
                gh_cmd = ["gh", "repo", "create", repo_name, "--source=.", visibility, "--push"]
                if description:
                    gh_cmd.extend(["--description", description])
                
                try:
                    result = subprocess.run(gh_cmd, capture_output=True, text=True, check=True)
                    self.log(f"✅ Repository created and pushed successfully!", 'success')
                    self.log(result.stdout, 'info')
                except subprocess.CalledProcessError as e:
                    err_msg = e.stderr if hasattr(e, 'stderr') else str(e)
                    if "Name already exists on this account" in err_msg:
                        self.log(f"⚠️ Repository already exists: {err_msg}", 'warning')
                        # Ask user what to do
                        reply = QMessageBox.question(self, "Repository Exists", 
                                                   f"Repository '{repo_name}' already exists. Force push?",
                                                   QMessageBox.Yes | QMessageBox.No)
                        if reply == QMessageBox.Yes:
                            try:
                                subprocess.run(["git", "push", "--force"], check=True, capture_output=True)
                                self.log("✅ Force push completed", 'success')
                            except subprocess.CalledProcessError as push_e:
                                self.log(f"❌ Force push failed: {push_e}", 'error')
                        else:
                            self.log("❌ Operation cancelled by user", 'warning')
                    else:
                        self.log(f"❌ GitHub Error: {err_msg}", 'error')
                        
            except Exception as e:
                self.log(f"❌ Unexpected error: {str(e)}", 'error')
        
        # Run in background thread
        threading.Thread(target=run_operation, daemon=True).start()

    def configure_git_credentials(self):
        """Configure Git credentials via dialog"""
        username, ok1 = QInputDialog.getText(self, "Git Username", "Enter your Git username:")
        if ok1 and username:
            email, ok2 = QInputDialog.getText(self, "Git Email", "Enter your Git email:")
            if ok2 and email:
                try:
                    subprocess.run(["git", "config", "--global", "user.name", username], 
                                 check=True, capture_output=True)
                    subprocess.run(["git", "config", "--global", "user.email", email], 
                                 check=True, capture_output=True)
                    self.git_username = username
                    self.git_email = email
                    self.log(f"✅ Git credentials configured: {username} <{email}>", 'success')
                except subprocess.CalledProcessError as e:
                    self.log(f"❌ Failed to configure Git: {e}", 'error')
            else:
                self.log("Git credentials configuration cancelled.", 'warning')
        else:
            self.log("Git credentials configuration cancelled.", 'warning')

    def configure_github_token(self):
        """Configure GitHub token via dialog"""
        token, ok = QInputDialog.getText(self, "GitHub Token", 
                                       "Enter your GitHub Personal Access Token:", 
                                       QLineEdit.Password)
        if ok and token:
            # Test the token
            try:
                headers = {
                    'Authorization': f'token {token}',
                    'Accept': 'application/vnd.github.v3+json'
                }
                response = requests.get('https://api.github.com/user', headers=headers)
                if response.status_code == 200:
                    user_data = response.json()
                    self.github_token = token
                    self.log(f"✅ GitHub token configured successfully! Authenticated as: {user_data['login']}", 'success')
                else:
                    self.log("❌ Invalid GitHub token. Please check your token and try again.", 'error')
            except Exception as e:
                self.log(f"❌ Failed to validate token: {str(e)}", 'error')
        else:
            self.log("GitHub token configuration cancelled.", 'warning')

    def get_text_dialog(self, title, label):
        # Simple input dialog for commit messages, etc.
        from PySide6.QtWidgets import QInputDialog
        return QInputDialog.getText(self, title, label)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 