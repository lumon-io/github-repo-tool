#!/usr/bin/env python3
"""
GitHub Repository Setup Tool
A tool to easily create and manage GitHub repositories from local folders.
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import subprocess
import git
from datetime import datetime
import argparse
import threading
import time
import json
import requests
from typing import Optional, Dict, List

# Add Pillow import for image support
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Add questionary for TUI
try:
    import questionary
    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False

# Add InquirerPy for TUI file explorer
try:
    from InquirerPy import inquirer as inquirerpy_inquirer
    INQUIRERPY_AVAILABLE = True
except ImportError:
    INQUIRERPY_AVAILABLE = False

# Add Textual for TUI file explorer
try:
    from textual.app import App, ComposeResult
    from textual.widgets import DirectoryTree, Footer, Header, Button, Static, Input
    from textual.containers import Container, Horizontal
    from textual.reactive import reactive
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

class GitHubRepoSetup:
    def __init__(self):
        self.root: Optional[tk.Tk] = None
        self.folder_var: Optional[tk.StringVar] = None
        self.status_label: Optional[tk.Label] = None
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.visibility_var: Optional[tk.StringVar] = None
        self.description_var: Optional[tk.StringVar] = None
        self.status_text: Optional[tk.Text] = None
        self.action_buttons_frame: Optional[ttk.Frame] = None
        self.git_username_var: Optional[tk.StringVar] = None
        self.git_email_var: Optional[tk.StringVar] = None
        self.github_token_var: Optional[tk.StringVar] = None
        self.icon_img = None  # For keeping a reference to the icon image
        
    def setup_mac_style(self):
        """Apply Mac-like styling to the application"""
        if not self.root:
            return
        
        # Configure colors
        self.colors = {
            'bg': '#f5f5f7',           # Light gray background
            'card_bg': '#ffffff',       # White card background
            'primary': '#007aff',       # Apple blue
            'secondary': '#5856d6',     # Purple
            'success': '#34c759',       # Green
            'warning': '#ff9500',       # Orange
            'danger': '#ff3b30',        # Red
            'text': '#1d1d1f',         # Dark text
            'text_secondary': '#86868b', # Secondary text
            'border': '#d2d2d7',       # Light border
            'hover': '#f2f2f7'         # Hover state
        }
        
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure common styles
        style.configure('Mac.TFrame', background=self.colors['bg'])
        style.configure('Mac.TLabel', background=self.colors['bg'], foreground=self.colors['text'])
        style.configure('Mac.TButton', 
                      background=self.colors['primary'], 
                      foreground='white',
                      borderwidth=0,
                      focuscolor='none',
                      font=('SF Pro Display', 10))
        
        style.map('Mac.TButton',
                 background=[('active', self.colors['secondary']),
                           ('pressed', self.colors['secondary'])])
        
        style.configure('Success.TButton',
                      background=self.colors['success'],
                      foreground='white')
        
        style.configure('Warning.TButton',
                      background=self.colors['warning'],
                      foreground='white')
        
        style.configure('Danger.TButton',
                      background=self.colors['danger'],
                      foreground='white')
        
        # Configure entry style
        style.configure('Mac.TEntry',
                      fieldbackground='white',
                      borderwidth=1,
                      relief='solid',
                      bordercolor=self.colors['border'])
        
        # Configure combobox style
        style.configure('Mac.TCombobox',
                      fieldbackground='white',
                      borderwidth=1,
                      relief='solid',
                      bordercolor=self.colors['border'])
        
        # Configure progress bar
        style.configure('Mac.Horizontal.TProgressbar',
                      background=self.colors['primary'],
                      troughcolor=self.colors['border'])

    def get_detailed_git_status(self, path):
        """Get comprehensive Git status for a path"""
        if not path or not os.path.isdir(path):
            return "⚠️ Please select a valid folder."
        try:
            repo = git.Repo(path)
            # Basic info
            status_info = []
            status_info.append("✅ Git repository found")
            # Branch info
            try:
                branch = repo.active_branch.name
                status_info.append(f"🌿 Current branch: {branch}")
            except Exception:
                status_info.append("🌿 No active branch (detached HEAD)")
            # Remote info
            if repo.remotes:
                remote_url = next(repo.remote().urls)
                status_info.append(f"🌐 Remote: {remote_url}")
            else:
                status_info.append("🌐 No remote configured")
            # Last commit
            try:
                last_commit = datetime.fromtimestamp(repo.head.commit.committed_date).strftime('%Y-%m-%d %H:%M:%S')
                status_info.append(f"📅 Last commit: {last_commit}")
                status_info.append(f"📝 Message: {repo.head.commit.message.strip()}")
            except Exception:
                status_info.append("📅 No commits yet")
            # Working directory status
            try:
                # Check for uncommitted changes
                if repo.is_dirty():
                    status_info.append("⚠️ Working directory has uncommitted changes")
                    # Show modified files
                    modified_files = [item.a_path for item in repo.index.diff(None)]
                    untracked_files = repo.untracked_files
                    if modified_files:
                        status_info.append(f"📝 Modified files: {len(modified_files)}")
                    if untracked_files:
                        status_info.append(f"🆕 Untracked files: {len(untracked_files)}")
                else:
                    status_info.append("✅ Working directory is clean")
                # Check if behind/ahead of remote
                if repo.remotes:
                    try:
                        remote = repo.remote()
                        remote.fetch()
                        local_commit = repo.head.commit
                        remote_commit = remote.refs[0].commit
                        if local_commit != remote_commit:
                            # Count commits ahead/behind
                            ahead = len(list(repo.iter_commits(f'{local_commit}..{remote_commit}')))
                            behind = len(list(repo.iter_commits(f'{remote_commit}..{local_commit}')))
                            if ahead > 0:
                                status_info.append(f"⬆️ {ahead} commits ahead of remote")
                            if behind > 0:
                                status_info.append(f"⬇️ {behind} commits behind remote")
                        else:
                            status_info.append("✅ Up to date with remote")
                    except Exception:
                        status_info.append("ℹ️ Could not check remote status")
            except Exception as e:
                status_info.append(f"⚠️ Error checking status: {str(e)}")
            return "\n".join(status_info)
        except git.exc.InvalidGitRepositoryError:
            return "⚠️ Not a Git repository.\n💡 Click 'Initialize Git' to start."
        except Exception as e:
            return f"⚠️ Git error: {str(e)}"

    def get_file_status(self, path):
        """Get detailed file status for display in text widget"""
        if not path or not os.path.isdir(path):
            return "No folder selected."
        try:
            repo = git.Repo(path)
            status_text = []
            # Working directory status
            if repo.is_dirty():
                status_text.append("=== MODIFIED FILES ===")
                for item in repo.index.diff(None):
                    status_text.append(f"📝 {item.a_path}")
                status_text.append("\n=== UNTRACKED FILES ===")
                for file in repo.untracked_files:
                    status_text.append(f"🆕 {file}")
                status_text.append("\n=== STAGED FILES ===")
                for item in repo.index.diff('HEAD'):
                    status_text.append(f"✅ {item.a_path}")
            else:
                status_text.append("✅ Working directory is clean")
            return "\n".join(status_text)
        except git.exc.InvalidGitRepositoryError:
            return "Not a Git repository."
        except Exception as e:
            return f"Error: {str(e)}"

    def get_github_repo_info(self, repo_path: str) -> Dict:
        """Get detailed GitHub repository information"""
        try:
            repo = git.Repo(repo_path)
            if not repo.remotes:
                return {"error": "No remote configured"}
            remote_url = next(repo.remote().urls)
            if 'github.com' not in remote_url:
                return {"error": "Not a GitHub repository"}
            # Extract owner and repo name from URL
            if remote_url.startswith('git@'):
                # SSH format: git@github.com:owner/repo.git
                parts = remote_url.replace('git@github.com:', '').replace('.git', '').split('/')
            else:
                # HTTPS format: https://github.com/owner/repo.git
                parts = remote_url.replace('https://github.com/', '').replace('.git', '').split('/')
            if len(parts) != 2:
                return {"error": "Invalid GitHub URL format"}
            owner, repo_name = parts
            # Get GitHub token from environment or config
            token = os.getenv('GITHUB_TOKEN') or self.get_github_token()
            if not token:
                return {"error": "GitHub token not configured"}
            # Fetch repository data from GitHub API
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                repo_data = response.json()
                # Get recent commits
                commits_url = f"{api_url}/commits"
                commits_response = requests.get(commits_url, headers=headers)
                recent_commits = []
                if commits_response.status_code == 200:
                    commits_data = commits_response.json()
                    for commit in commits_data[:5]:  # Last 5 commits
                        recent_commits.append({
                            'sha': commit['sha'][:7],
                            'message': commit['commit']['message'],
                            'author': commit['commit']['author']['name'],
                            'date': commit['commit']['author']['date']
                        })
                # Get pull requests
                prs_url = f"{api_url}/pulls"
                prs_response = requests.get(prs_url, headers=headers)
                pull_requests = []
                if prs_response.status_code == 200:
                    prs_data = prs_response.json()
                    for pr in prs_data[:5]:  # Last 5 PRs
                        pull_requests.append({
                            'number': pr['number'],
                            'title': pr['title'],
                            'state': pr['state'],
                            'user': pr['user']['login']
                        })
                # Get issues
                issues_url = f"{api_url}/issues"
                issues_response = requests.get(issues_url, headers=headers)
                issues = []
                if issues_response.status_code == 200:
                    issues_data = issues_response.json()
                    for issue in issues_data[:5]:  # Last 5 issues
                        issues.append({
                            'number': issue['number'],
                            'title': issue['title'],
                            'state': issue['state'],
                            'user': issue['user']['login']
                        })
                return {
                    'name': repo_data['name'],
                    'full_name': repo_data['full_name'],
                    'description': repo_data['description'],
                    'language': repo_data['language'],
                    'stars': repo_data['stargazers_count'],
                    'forks': repo_data['forks_count'],
                    'open_issues': repo_data['open_issues_count'],
                    'private': repo_data['private'],
                    'created_at': repo_data['created_at'],
                    'updated_at': repo_data['updated_at'],
                    'recent_commits': recent_commits,
                    'pull_requests': pull_requests,
                    'issues': issues,
                    'url': repo_data['html_url']
                }
            else:
                return {"error": f"Failed to fetch repository data: {response.status_code}"}
        except Exception as e:
            return {"error": f"Error fetching GitHub data: {str(e)}"}

    def get_github_token(self) -> Optional[str]:
        """Get GitHub token from various sources"""
        # Try environment variable
        token = os.getenv('GITHUB_TOKEN')
        if token:
            return token
        # Try GitHub CLI config
        try:
            result = subprocess.run(['gh', 'auth', 'token'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except Exception:
            pass
        # Try git config
        try:
            result = subprocess.run(['git', 'config', '--global', 'github.token'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def show_github_details(self):
        """Show detailed GitHub repository information"""
        if not self.folder_var:
            return
        folder = self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder first.")
            return
        # Show loading message
        loading_window = tk.Toplevel(self.root)
        loading_window.title("Loading GitHub Data")
        loading_window.geometry("300x100")
        loading_window.configure(bg=self.colors['bg'])
        loading_window.transient(self.root)
        loading_window.grab_set()
        loading_label = tk.Label(loading_window, text="Fetching GitHub data...", 
                               font=("SF Pro Display", 12), 
                               fg=self.colors['text'], bg=self.colors['bg'])
        loading_label.pack(expand=True)
        def fetch_data():
            try:
                repo_info = self.get_github_repo_info(folder)
                # Update UI in main thread
                if self.root:
                    self.root.after(0, lambda: show_github_window(repo_info))
            except Exception as e:
                if self.root:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch GitHub data: {str(e)}"))
            finally:
                if self.root:
                    self.root.after(0, loading_window.destroy)
        def show_github_window(repo_info):
            if 'error' in repo_info:
                messagebox.showerror("GitHub Error", repo_info['error'])
                return
            # Create detailed GitHub window
            github_window = tk.Toplevel(self.root)
            github_window.title(f"GitHub: {repo_info['full_name']}")
            github_window.geometry("800x600")
            github_window.configure(bg=self.colors['bg'])
            # Create notebook for tabs
            notebook = ttk.Notebook(github_window)
            notebook.pack(fill="both", expand=True, padx=10, pady=10)
            # Overview tab
            overview_frame = ttk.Frame(notebook)
            notebook.add(overview_frame, text="Overview")
            overview_text = tk.Text(overview_frame, wrap=tk.WORD, 
                                  font=("SF Mono", 10),
                                  bg='white', fg=self.colors['text'])
            overview_scrollbar = ttk.Scrollbar(overview_frame, orient="vertical", 
                                             command=overview_text.yview)
            overview_text.configure(yscrollcommand=overview_scrollbar.set)
            overview_text.pack(side="left", fill="both", expand=True)
            overview_scrollbar.pack(side="right", fill="y")
            # Format overview data
            overview_data = f"""🚀 GitHub Repository: {repo_info['full_name']}

📝 Description: {repo_info['description'] or 'No description'}
🔤 Language: {repo_info['language'] or 'Unknown'}
⭐ Stars: {repo_info['stars']}
🍴 Forks: {repo_info['forks']}
🐛 Open Issues: {repo_info['open_issues']}
🔒 Private: {'Yes' if repo_info['private'] else 'No'}

📅 Created: {repo_info['created_at']}
🔄 Updated: {repo_info['updated_at']}

🌐 URL: {repo_info['url']}
"""
            overview_text.insert("1.0", overview_data)
            overview_text.config(state="disabled")
            # Recent commits tab
            commits_frame = ttk.Frame(notebook)
            notebook.add(commits_frame, text="Recent Commits")
            commits_text = tk.Text(commits_frame, wrap=tk.WORD, 
                                 font=("SF Mono", 10),
                                 bg='white', fg=self.colors['text'])
            commits_scrollbar = ttk.Scrollbar(commits_frame, orient="vertical", 
                                            command=commits_text.yview)
            commits_text.configure(yscrollcommand=commits_scrollbar.set)
            commits_text.pack(side="left", fill="both", expand=True)
            commits_scrollbar.pack(side="right", fill="y")
            commits_data = "📝 Recent Commits:\n\n"
            for commit in repo_info['recent_commits']:
                commits_data += f"🔸 {commit['sha']} - {commit['message']}\n"
                commits_data += f"   👤 {commit['author']} - {commit['date']}\n\n"
            commits_text.insert("1.0", commits_data)
            commits_text.config(state="disabled")
            # Pull requests tab
            prs_frame = ttk.Frame(notebook)
            notebook.add(prs_frame, text="Pull Requests")
            prs_text = tk.Text(prs_frame, wrap=tk.WORD, 
                             font=("SF Mono", 10),
                             bg='white', fg=self.colors['text'])
            prs_scrollbar = ttk.Scrollbar(prs_frame, orient="vertical", 
                                         command=prs_text.yview)
            prs_text.configure(yscrollcommand=prs_scrollbar.set)
            prs_text.pack(side="left", fill="both", expand=True)
            prs_scrollbar.pack(side="right", fill="y")
            prs_data = "🔀 Pull Requests:\n\n"
            for pr in repo_info['pull_requests']:
                status_emoji = "🟢" if pr['state'] == 'open' else "🔴"
                prs_data += f"{status_emoji} #{pr['number']} - {pr['title']}\n"
                prs_data += f"   👤 {pr['user']} - {pr['state']}\n\n"
            prs_text.insert("1.0", prs_data)
            prs_text.config(state="disabled")
            # Issues tab
            issues_frame = ttk.Frame(notebook)
            notebook.add(issues_frame, text="Issues")
            issues_text = tk.Text(issues_frame, wrap=tk.WORD, 
                                font=("SF Mono", 10),
                                bg='white', fg=self.colors['text'])
            issues_scrollbar = ttk.Scrollbar(issues_frame, orient="vertical", 
                                           command=issues_text.yview)
            issues_text.configure(yscrollcommand=issues_scrollbar.set)
            issues_text.pack(side="left", fill="both", expand=True)
            issues_scrollbar.pack(side="right", fill="y")
            issues_data = "🐛 Issues:\n\n"
            for issue in repo_info['issues']:
                status_emoji = "🟢" if issue['state'] == 'open' else "🔴"
                issues_data += f"{status_emoji} #{issue['number']} - {issue['title']}\n"
                issues_data += f"   👤 {issue['user']} - {issue['state']}\n\n"
            issues_text.insert("1.0", issues_data)
            issues_text.config(state="disabled")
        # Run in background thread
        threading.Thread(target=fetch_data, daemon=True).start()

    def configure_github_token(self):
        """Configure GitHub token via UI"""
        if not self.github_token_var:
            return
        # Create token configuration window
        token_window = tk.Toplevel(self.root)
        token_window.title("Configure GitHub Token")
        token_window.geometry("500x300")
        token_window.configure(bg=self.colors['bg'])
        token_window.resizable(False, False)
        # Center the window
        token_window.transient(self.root)
        token_window.grab_set()
        # Main frame
        main_frame = ttk.Frame(token_window, style='Mac.TFrame')
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        # Title
        title_label = tk.Label(main_frame, text="GitHub Token Configuration", 
                             font=("SF Pro Display", 16, "bold"), 
                             fg=self.colors['text'], bg=self.colors['bg'])
        title_label.pack(pady=(0, 10))
        # Instructions
        instructions = tk.Label(main_frame, 
                              text="Enter your GitHub Personal Access Token.\nThis is required for detailed GitHub data.", 
                              font=("SF Pro Display", 10), 
                              fg=self.colors['text_secondary'], bg=self.colors['bg'],
                              justify=tk.CENTER)
        instructions.pack(pady=(0, 20))
        # Token entry
        token_frame = ttk.Frame(main_frame)
        token_frame.pack(fill="x", pady=5)
        ttk.Label(token_frame, text="GitHub Token:", style='Mac.TLabel').pack(anchor="w")
        token_entry = ttk.Entry(token_frame, textvariable=self.github_token_var, 
                              style='Mac.TEntry', width=50, show="*")
        token_entry.pack(fill="x", pady=2)
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)
        def save_token():
            if not self.github_token_var:
                return
            token = self.github_token_var.get()
            if not token:
                messagebox.showerror("Error", "Please enter a GitHub token.")
                return
            try:
                # Test the token by making a simple API call
                headers = {
                    'Authorization': f'token {token}',
                    'Accept': 'application/vnd.github.v3+json'
                }
                response = requests.get('https://api.github.com/user', headers=headers)
                if response.status_code == 200:
                    user_data = response.json()
                    messagebox.showinfo("Success", f"✅ GitHub token configured successfully!\nAuthenticated as: {user_data['login']}")
                    token_window.destroy()
                else:
                    messagebox.showerror("Error", "Invalid GitHub token. Please check your token and try again.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to validate token: {str(e)}")
        def cancel():
            token_window.destroy()
        save_btn = ttk.Button(button_frame, text="Save", command=save_token, 
                             style='Mac.TButton')
        save_btn.pack(side="right", padx=(5, 0))
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=cancel)
        cancel_btn.pack(side="right")
        # Load current token if available
        current_token = self.get_github_token()
        if current_token:
            self.github_token_var.set(current_token)

    def configure_git_credentials(self):
        """Configure Git credentials via UI"""
        if not self.git_username_var or not self.git_email_var:
            return
        # Create credential configuration window
        cred_window = tk.Toplevel(self.root)
        cred_window.title("Configure Git Credentials")
        cred_window.geometry("400x300")
        cred_window.configure(bg=self.colors['bg'])
        cred_window.resizable(False, False)
        # Center the window
        cred_window.transient(self.root)
        cred_window.grab_set()
        # Main frame
        main_frame = ttk.Frame(cred_window, style='Mac.TFrame')
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        # Title
        title_label = tk.Label(main_frame, text="Git Configuration", 
                             font=("SF Pro Display", 16, "bold"), 
                             fg=self.colors['text'], bg=self.colors['bg'])
        title_label.pack(pady=(0, 20))
        # Username
        username_frame = ttk.Frame(main_frame)
        username_frame.pack(fill="x", pady=5)
        ttk.Label(username_frame, text="Username:", style='Mac.TLabel').pack(anchor="w")
        username_entry = ttk.Entry(username_frame, textvariable=self.git_username_var, 
                                 style='Mac.TEntry', width=30)
        username_entry.pack(fill="x", pady=2)
        # Email
        email_frame = ttk.Frame(main_frame)
        email_frame.pack(fill="x", pady=5)
        ttk.Label(email_frame, text="Email:", style='Mac.TLabel').pack(anchor="w")
        email_entry = ttk.Entry(email_frame, textvariable=self.git_email_var, 
                              style='Mac.TEntry', width=30)
        email_entry.pack(fill="x", pady=2)
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)
        def save_credentials():
            if not self.git_username_var or not self.git_email_var:
                return
            username = self.git_username_var.get()
            email = self.git_email_var.get()
            if not username or not email:
                messagebox.showerror("Error", "Please enter both username and email.")
                return
            try:
                # Configure Git globally
                subprocess.run(["git", "config", "--global", "user.name", username], 
                             check=True, capture_output=True)
                subprocess.run(["git", "config", "--global", "user.email", email], 
                             check=True, capture_output=True)
                messagebox.showinfo("Success", "✅ Git credentials configured successfully!")
                cred_window.destroy()
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Failed to configure Git: {e}")
        def cancel():
            cred_window.destroy()
        save_btn = ttk.Button(button_frame, text="Save", command=save_credentials, 
                             style='Mac.TButton')
        save_btn.pack(side="right", padx=(5, 0))
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=cancel)
        cancel_btn.pack(side="right")
        # Load current values
        try:
            username_result = subprocess.run(["git", "config", "--global", "user.name"], 
                                          capture_output=True, text=True)
            if username_result.returncode == 0:
                self.git_username_var.set(username_result.stdout.strip())
            email_result = subprocess.run(["git", "config", "--global", "user.email"], 
                                        capture_output=True, text=True)
            if email_result.returncode == 0:
                self.git_email_var.set(email_result.stdout.strip())
        except Exception:
            pass

    def initialize_git(self):
        """Initialize Git repository in the selected folder"""
        if not self.folder_var:
            return
        folder = self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder.")
            return
        try:
            os.chdir(folder)
            subprocess.run(["git", "init"], check=True, capture_output=True)
            messagebox.showinfo("Success", "✅ Git repository initialized!")
            self.update_status()
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to initialize Git: {e}")

    def git_pull(self):
        """Pull latest changes from remote"""
        if not self.folder_var:
            return
        folder = self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder.")
            return
        try:
            os.chdir(folder)
            result = subprocess.run(["git", "pull"], capture_output=True, text=True, check=True)
            messagebox.showinfo("Success", f"✅ Pull successful!\n{result.stdout}")
            self.update_status()
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Pull failed: {e.stderr}")

    def git_push(self):
        """Push changes to remote"""
        if not self.folder_var:
            return
        folder = self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder.")
            return
        try:
            os.chdir(folder)
            result = subprocess.run(["git", "push"], capture_output=True, text=True, check=True)
            messagebox.showinfo("Success", f"✅ Push successful!\n{result.stdout}")
            self.update_status()
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Push failed: {e.stderr}")

    def git_add_all(self):
        """Add all files to staging"""
        if not self.folder_var:
            return
        folder = self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder.")
            return
        try:
            os.chdir(folder)
            subprocess.run(["git", "add", "."], check=True, capture_output=True)
            messagebox.showinfo("Success", "✅ All files added to staging!")
            self.update_status()
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to add files: {e}")

    def git_commit(self):
        """Commit staged changes"""
        if not self.folder_var:
            return
        folder = self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder.")
            return
        # Get commit message from user
        commit_msg = simpledialog.askstring("Commit Message", "Enter commit message:")
        if not commit_msg:
            return
        try:
            os.chdir(folder)
            subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
            messagebox.showinfo("Success", "✅ Changes committed!")
            self.update_status()
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Commit failed: {e}")

    def git_status(self):
        """Show detailed git status"""
        if not self.folder_var:
            return
        folder = self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder.")
            return
        try:
            os.chdir(folder)
            result = subprocess.run(["git", "status"], capture_output=True, text=True, check=True)
            # Create a new window to show status
            status_window = tk.Toplevel(self.root)
            status_window.title("Git Status")
            status_window.geometry("600x400")
            status_window.configure(bg=self.colors['bg'])
            text_widget = tk.Text(status_window, wrap=tk.WORD, 
                                bg='white', fg=self.colors['text'],
                                font=('SF Mono', 10))
            scrollbar = ttk.Scrollbar(status_window, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            text_widget.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            scrollbar.pack(side="right", fill="y", pady=10)
            text_widget.insert("1.0", result.stdout)
            text_widget.config(state="disabled")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to get status: {e}")

    def create_or_push_repo(self):
        """Create GitHub repository and push code"""
        if not self.folder_var or not self.visibility_var or not self.description_var or not self.progress_bar or not self.root:
            return
        folder = self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder.")
            return
        # Show progress
        self.progress_bar.start()
        def run_operation():
            try:
                os.chdir(folder)
                # Check if Git is initialized
                try:
                    repo = git.Repo(folder)
                    is_git_repo = True
                except git.exc.InvalidGitRepositoryError:
                    subprocess.run(["git", "init"], check=True, capture_output=True)
                    repo = git.Repo(folder)
                    is_git_repo = False
                # Add all files
                repo.git.add(A=True)
                # Commit if there are changes
                try:
                    commit_message = "Initial commit" if not is_git_repo else "Update repository"
                    repo.index.commit(commit_message)
                except git.exc.GitCommandError:
                    pass  # No changes to commit
                # Create GitHub repository
                repo_name = os.path.basename(folder)
                if not self.visibility_var or not self.description_var:
                    return
                visibility = "--public" if self.visibility_var.get() == "Public" else "--private"
                description = self.description_var.get()
                gh_cmd = ["gh", "repo", "create", repo_name, "--source=.", visibility, "--push"]
                if description:
                    gh_cmd.extend(["--description", description])
                result = subprocess.run(gh_cmd, capture_output=True, text=True, check=True)
                # Update UI in main thread
                if self.root:
                    self.root.after(0, lambda: self.show_success(result.stdout))
            except subprocess.CalledProcessError as e:
                if self.root:
                    self.root.after(0, lambda: self.show_error(f"GitHub Error: {e.stderr}"))
            except Exception as e:
                if self.root:
                    self.root.after(0, lambda: self.show_error(f"Unexpected error: {str(e)}"))
            finally:
                if self.root and self.progress_bar:
                    self.root.after(0, self.progress_bar.stop)
                    self.root.after(0, self.update_status)
        # Run in background thread
        threading.Thread(target=run_operation, daemon=True).start()

    def show_success(self, message):
        """Show success message"""
        messagebox.showinfo("Success", f"✅ Repository created and pushed!\n{message}")

    def show_error(self, message):
        """Show error message"""
        messagebox.showerror("Error", message)

    def update_status(self):
        """Update the status display"""
        if not self.folder_var or not self.status_label or not self.status_text:
            return
        status = self.get_detailed_git_status(self.folder_var.get())
        self.status_label.config(text=status)
        # Update file status in text widget
        file_status = self.get_file_status(self.folder_var.get())
        self.status_text.config(state="normal")
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert("1.0", file_status)
        self.status_text.config(state="disabled")

    def browse_folder(self):
        """Open folder browser dialog"""
        folder = filedialog.askdirectory()
        if folder and self.folder_var:
            self.folder_var.set(folder)
            self.update_status()

    def open_in_explorer(self):
        """Open the selected folder in file explorer"""
        if not self.folder_var:
            return
        folder = self.folder_var.get()
        if folder and os.path.isdir(folder):
            os.startfile(folder) if os.name == 'nt' else subprocess.run(['xdg-open', folder])
        else:
            messagebox.showerror("Error", "Please select a valid folder first.")

    def open_in_github(self):
        """Open the repository in GitHub (if it exists)"""
        if not self.folder_var:
            return
        folder = self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder first.")
            return
        try:
            repo = git.Repo(folder)
            remote_url = next(repo.remote().urls)
            if 'github.com' in remote_url:
                # Convert SSH to HTTPS if needed
                if remote_url.startswith('git@'):
                    remote_url = remote_url.replace('git@github.com:', 'https://github.com/').replace('.git', '')
                subprocess.run(['start', remote_url] if os.name == 'nt' else ['xdg-open', remote_url])
            else:
                messagebox.showinfo("Info", "No GitHub remote found for this repository.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open GitHub: {str(e)}")

    def setup_ui(self):
        """Setup the GUI"""
        self.root = tk.Tk()
        self.root.title("GitHub Repository Setup Tool")
        self.root.geometry("900x750")
        self.root.resizable(True, True)
        
        # Set window icon if Pillow and icon file are available
        icon_path = os.path.join(os.path.dirname(__file__), "octocat.png")
        if PIL_AVAILABLE and os.path.exists(icon_path):
            try:
                pil_img = Image.open(icon_path)
                self.icon_img = ImageTk.PhotoImage(pil_img)
                self.root.iconphoto(True, self.icon_img)
            except Exception:
                pass
        
        # Apply Mac styling
        self.setup_mac_style()
        self.root.configure(bg=self.colors['bg'])
        
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(7, weight=1)

        # Title with icon
        title_frame = ttk.Frame(self.root, style='Mac.TFrame')
        title_frame.grid(row=0, column=0, pady=20)
        
        # Add Octocat icon to header if available
        if PIL_AVAILABLE and os.path.exists(icon_path):
            try:
                pil_img = Image.open(icon_path).resize((48, 48))
                self.header_icon_img = ImageTk.PhotoImage(pil_img)
                icon_label = tk.Label(title_frame, image=self.header_icon_img, bg=self.colors['bg'])
                icon_label.pack(side="left", padx=(0, 10))
            except Exception:
                pass
        
        title_label = tk.Label(title_frame, text="🚀 GitHub Repository Setup Tool", 
                             font=("SF Pro Display", 20, "bold"), 
                             fg=self.colors['text'], bg=self.colors['bg'])
        title_label.pack(side="left")
        
        subtitle_label = tk.Label(title_frame, text="Manage your Git repositories with style", 
                                font=("SF Pro Display", 12), 
                                fg=self.colors['text_secondary'], bg=self.colors['bg'])
        subtitle_label.pack(anchor="w", padx=(0, 0))

        # Folder selection card
        folder_card = ttk.Frame(self.root, style='Mac.TFrame')
        folder_card.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        folder_frame = ttk.LabelFrame(folder_card, text="📁 Project Folder", padding=15)
        folder_frame.pack(fill="x", padx=10, pady=5)
        folder_frame.grid_columnconfigure(0, weight=1)

        self.folder_var = tk.StringVar()
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, 
                               style='Mac.TEntry', width=50)
        folder_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        browse_btn = ttk.Button(folder_frame, text="Browse", command=self.browse_folder, 
                               style='Mac.TButton')
        browse_btn.grid(row=0, column=1)

        # Repository options card
        options_card = ttk.Frame(self.root, style='Mac.TFrame')
        options_card.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        options_frame = ttk.LabelFrame(options_card, text="⚙️ Repository Options", padding=15)
        options_frame.pack(fill="x", padx=10, pady=5)
        options_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(options_frame, text="Visibility:", style='Mac.TLabel').grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.visibility_var = tk.StringVar(value="Public")
        visibility_combo = ttk.Combobox(options_frame, textvariable=self.visibility_var, 
                                      values=["Public", "Private"], state="readonly", 
                                      style='Mac.TCombobox', width=15)
        visibility_combo.grid(row=0, column=1, sticky="w")

        ttk.Label(options_frame, text="Description:", style='Mac.TLabel').grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(15, 0))
        self.description_var = tk.StringVar()
        description_entry = ttk.Entry(options_frame, textvariable=self.description_var, 
                                    style='Mac.TEntry', width=40)
        description_entry.grid(row=1, column=1, sticky="ew", pady=(15, 0))

        # Git credentials
        self.git_username_var = tk.StringVar()
        self.git_email_var = tk.StringVar()
        self.github_token_var = tk.StringVar()
        
        cred_card = ttk.Frame(self.root, style='Mac.TFrame')
        cred_card.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        cred_frame = ttk.LabelFrame(cred_card, text="👤 Git Credentials", padding=15)
        cred_frame.pack(fill="x", padx=10, pady=5)
        
        cred_btn = ttk.Button(cred_frame, text="Configure Git Credentials", 
                             command=self.configure_git_credentials, style='Mac.TButton')
        cred_btn.pack()
        
        github_token_btn = ttk.Button(cred_frame, text="Configure GitHub Token", 
                                    command=self.configure_github_token, style='Mac.TButton')
        github_token_btn.pack(pady=(5, 0))

        # Git management card
        git_card = ttk.Frame(self.root, style='Mac.TFrame')
        git_card.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        git_frame = ttk.LabelFrame(git_card, text="🛠️ Git Management", padding=15)
        git_frame.pack(fill="x", padx=10, pady=5)
        
        # Row 1: Basic Git operations
        git_row1 = ttk.Frame(git_frame)
        git_row1.pack(fill="x", pady=5)
        
        init_btn = ttk.Button(git_row1, text="Initialize Git", command=self.initialize_git, 
                             style='Mac.TButton')
        init_btn.pack(side=tk.LEFT, padx=3)
        
        status_btn = ttk.Button(git_row1, text="Git Status", command=self.git_status, 
                               style='Mac.TButton')
        status_btn.pack(side=tk.LEFT, padx=3)
        
        add_btn = ttk.Button(git_row1, text="Add All Files", command=self.git_add_all, 
                            style='Mac.TButton')
        add_btn.pack(side=tk.LEFT, padx=3)
        
        commit_btn = ttk.Button(git_row1, text="Commit Changes", command=self.git_commit, 
                               style='Mac.TButton')
        commit_btn.pack(side=tk.LEFT, padx=3)
        
        # Row 2: Remote operations
        git_row2 = ttk.Frame(git_frame)
        git_row2.pack(fill="x", pady=5)
        
        pull_btn = ttk.Button(git_row2, text="Pull from Remote", command=self.git_pull, 
                             style='Mac.TButton')
        pull_btn.pack(side=tk.LEFT, padx=3)
        
        push_btn = ttk.Button(git_row2, text="Push to Remote", command=self.git_push, 
                             style='Mac.TButton')
        push_btn.pack(side=tk.LEFT, padx=3)
        
        create_btn = ttk.Button(git_row2, text="Create & Push to GitHub", 
                               command=self.create_or_push_repo, style='Success.TButton')
        create_btn.pack(side=tk.LEFT, padx=3)
        
        # Row 3: Quick actions
        git_row3 = ttk.Frame(git_frame)
        git_row3.pack(fill="x", pady=5)
        
        explorer_btn = ttk.Button(git_row3, text="Open Folder", command=self.open_in_explorer, 
                                 style='Mac.TButton')
        explorer_btn.pack(side=tk.LEFT, padx=3)
        
        github_btn = ttk.Button(git_row3, text="Open in GitHub", command=self.open_in_github, 
                               style='Mac.TButton')
        github_btn.pack(side=tk.LEFT, padx=3)
        
        github_details_btn = ttk.Button(git_row3, text="GitHub Details", command=self.show_github_details, 
                                      style='Mac.TButton')
        github_details_btn.pack(side=tk.LEFT, padx=3)

        # Progress bar
        self.progress_bar = ttk.Progressbar(self.root, mode='indeterminate', 
                                          style='Mac.Horizontal.TProgressbar')
        self.progress_bar.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

        # Status display card
        status_card = ttk.Frame(self.root, style='Mac.TFrame')
        status_card.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        
        status_frame = ttk.LabelFrame(status_card, text="📊 Repository Status", padding=15)
        status_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = tk.Label(status_frame, text="No folder selected.", 
                                   justify=tk.LEFT, wraplength=800,
                                   font=("SF Pro Display", 10),
                                   fg=self.colors['text'], bg='white')
        self.status_label.grid(row=0, column=0, sticky="ew")

        # File status display card
        file_status_card = ttk.Frame(self.root, style='Mac.TFrame')
        file_status_card.grid(row=7, column=0, padx=20, pady=10, sticky="ew")
        
        file_status_frame = ttk.LabelFrame(file_status_card, text="📁 File Status", padding=15)
        file_status_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        file_status_frame.grid_columnconfigure(0, weight=1)
        file_status_frame.grid_rowconfigure(0, weight=1)
        
        # Create text widget with scrollbar for file status
        text_frame = ttk.Frame(file_status_frame)
        text_frame.grid(row=0, column=0, sticky="nsew")
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        
        self.status_text = tk.Text(text_frame, height=8, wrap=tk.WORD,
                                 font=("SF Mono", 9),
                                 bg='white', fg=self.colors['text'])
        status_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scrollbar.set)
        
        self.status_text.grid(row=0, column=0, sticky="nsew")
        status_scrollbar.grid(row=0, column=1, sticky="ns")

        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Browse Folder", command=self.browse_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=lambda: self.root.quit() if self.root else None)
        
        git_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Git", menu=git_menu)
        git_menu.add_command(label="Configure Credentials", command=self.configure_git_credentials)
        git_menu.add_separator()
        git_menu.add_command(label="Initialize Git", command=self.initialize_git)
        git_menu.add_command(label="Git Status", command=self.git_status)
        git_menu.add_command(label="Add All Files", command=self.git_add_all)
        git_menu.add_command(label="Commit Changes", command=self.git_commit)
        git_menu.add_separator()
        git_menu.add_command(label="Pull from Remote", command=self.git_pull)
        git_menu.add_command(label="Push to Remote", command=self.git_push)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

        # Keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.browse_folder())
        self.root.bind('<Control-q>', lambda e: self.root.quit() if self.root else None)
        self.root.bind('<Escape>', lambda e: self.root.quit() if self.root else None)

    def show_about(self):
        """Show about dialog"""
        about_text = """🚀 GitHub Repository Setup Tool v1.2

A beautiful and comprehensive tool to create and manage GitHub repositories.

Features:
• Initialize Git repositories
• Create GitHub repositories
• Push/pull from remote
• View detailed status
• Manage file staging
• Commit changes
• Configure Git credentials
• Open folders and repositories

Keyboard shortcuts:
• Ctrl+O: Browse folder
• Ctrl+Q: Quit
• Esc: Quit

Requirements:
• Git installed and configured
• GitHub CLI (gh) installed and authenticated"""
        
        messagebox.showinfo("About", about_text)

    def run_gui(self):
        """Run the GUI application"""
        self.setup_ui()
        if self.root:
            self.root.mainloop()

def run_command_line(folder_path, visibility="public", description="", push=True):
    """Run the tool from command line with a modern TUI header."""
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return False

    print("\n🐙 GitHub Repository Setup Tool - CLI Mode\n" + "=" * 50 + "\n")

    try:
        os.chdir(folder_path)
        
        # Initialize Git if needed
        try:
            repo = git.Repo(folder_path)
            print("✅ Git repository found")
        except git.exc.InvalidGitRepositoryError:
            print("📁 Initializing Git repository...")
            subprocess.run(["git", "init"], check=True, capture_output=True)
            repo = git.Repo(folder_path)
            print("✅ Git repository initialized")

        # Add and commit files
        repo.git.add(A=True)
        try:
            commit_message = "Initial commit"
            repo.index.commit(commit_message)
            print("✅ Files committed")
        except git.exc.GitCommandError:
            print("ℹ️ No changes to commit")

        # Create GitHub repository
        repo_name = os.path.basename(folder_path)
        print(f"🐙 Creating GitHub repository '{repo_name}'...")
        
        gh_cmd = ["gh", "repo", "create", repo_name, "--source=.", f"--{visibility}"]
        if description:
            gh_cmd.extend(["--description", description])
        if push:
            gh_cmd.append("--push")
        
        result = subprocess.run(gh_cmd, capture_output=True, text=True, check=True)
        print("✅ Repository created successfully!")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def detect_environment():
    """Detect if GUI is available and return environment type"""
    try:
        # Check if we're in a GUI environment
        if os.name == 'nt':  # Windows
            # Check if we have a display
            import tkinter
            root = tkinter.Tk()
            root.withdraw()  # Hide the test window
            root.destroy()
            return "gui_available"
        else:  # Unix/Linux/macOS
            # Check if DISPLAY is set (X11) or if we're on macOS
            if os.getenv('DISPLAY') or sys.platform == 'darwin':
                try:
                    import tkinter
                    root = tkinter.Tk()
                    root.withdraw()
                    root.destroy()
                    return "gui_available"
                except:
                    return "cli_only"
            else:
                return "cli_only"
    except:
        return "cli_only"

def prompt_user_mode():
    """Prompt user to choose between GUI and CLI mode using questionary if available."""
    if QUESTIONARY_AVAILABLE:
        print("\n🐙 GitHub Repository Setup Tool\n" + "="*40)
        choice = questionary.select(
            "Choose your preferred mode:",
            choices=[
                "GUI Mode - Beautiful graphical interface",
                "CLI Mode - Command line interface",
                "Exit"
            ]
        ).ask()
        if choice is None or choice == "Exit":
            return "exit"
        elif choice.startswith("GUI"):
            return "gui"
        elif choice.startswith("CLI"):
            return "cli"
    else:
        print("\n🐙 GitHub Repository Setup Tool\n" + "="*40)
        print("Choose your preferred mode:")
        print("1. GUI Mode - Beautiful graphical interface")
        print("2. CLI Mode - Command line interface")
        print("3. Exit")
        print()
        while True:
            try:
                choice = input("Enter your choice (1-3): ").strip()
                if choice == "1":
                    return "gui"
                elif choice == "2":
                    return "cli"
                elif choice == "3":
                    return "exit"
                else:
                    print("❌ Invalid choice. Please enter 1, 2, or 3.")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return "exit"

def pick_folder_inquirerpy():
    """Use InquirerPy to pick a folder in a simple, user-friendly TUI. Defaults to home directory and handles permission errors."""
    from InquirerPy import inquirer as inquirerpy_inquirer
    import os
    home = os.path.expanduser("~")
    while True:
        try:
            folder = inquirerpy_inquirer.filepath(
                message="Select your project folder:",
                only_directories=True,
                validate=lambda p: os.path.isdir(p),
                instruction="Use arrows to navigate, type to search, Tab to autocomplete, Enter to select, Esc to cancel, / to show folder list.",
                default=home
            ).execute()
            if folder and os.path.isdir(folder):
                return folder
            else:
                print("❌ No folder selected or invalid directory. Please try again.")
        except (PermissionError, OSError):
            print("⚠️ Some folders could not be listed due to permissions. Please select a different folder.")
            continue

def prompt_for_folder_cli():
    """Prompt the user for a folder path in CLI mode using InquirerPy if available, then Textual, then questionary/manual as fallback."""
    if INQUIRERPY_AVAILABLE:
        return pick_folder_inquirerpy()
    elif TEXTUAL_AVAILABLE:
        folder = pick_folder_textual()
        if folder and os.path.isdir(folder):
            return folder
        else:
            print("❌ No folder selected or invalid directory. Please try again.")
            return prompt_for_folder_cli()
    elif QUESTIONARY_AVAILABLE:
        while True:
            folder = questionary.path(
                "Select your project folder:",
                only_directories=True
            ).ask()
            if folder and os.path.isdir(folder):
                return folder
            else:
                print("❌ No folder selected or invalid directory. Please try again.")
    else:
        while True:
            try:
                folder = input("Please enter the path to your project folder (or leave blank to browse): ").strip()
                if folder:
                    if os.path.isdir(folder):
                        return folder
                    else:
                        print("❌ That path is not a valid directory. Please try again.")
                else:
                    # Try to open a folder dialog if possible
                    try:
                        import tkinter as tk
                        from tkinter import filedialog
                        root = tk.Tk()
                        root.withdraw()
                        folder = filedialog.askdirectory(title="Select Project Folder")
                        root.destroy()
                        if folder and os.path.isdir(folder):
                            return folder
                        else:
                            print("❌ No folder selected. Please try again.")
                    except Exception:
                        print("❌ Could not open folder dialog. Please enter the path manually.")
            except KeyboardInterrupt:
                print("\n👋 Cancelled by user.")
                sys.exit(0)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="GitHub Repository Setup Tool")
    parser.add_argument("folder", nargs="?", help="Folder path to setup as GitHub repository")
    parser.add_argument("--private", action="store_true", help="Create private repository (default: public)")
    parser.add_argument("--description", "-d", help="Repository description")
    parser.add_argument("--no-push", action="store_true", help="Don't push code after creation")
    parser.add_argument("--gui", action="store_true", help="Launch GUI mode")
    parser.add_argument("--cli", action="store_true", help="Force CLI mode")
    
    args = parser.parse_args()
    
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

    # Determine run mode
    if args.gui:
        # Force GUI mode
        run_mode = "gui"
    elif args.cli:
        # Force CLI mode
        run_mode = "cli"
    elif args.folder:
        # If folder is specified, run in CLI mode
        run_mode = "cli"
    else:
        # No specific mode requested, detect environment and ask user
        env_type = detect_environment()
        
        if env_type == "cli_only":
            print("🖥️  CLI-only environment detected. Running in command-line mode.")
            run_mode = "cli"
        elif env_type == "gui_available":
            # Ask user for preference
            run_mode = prompt_user_mode()
            if run_mode == "exit":
                return 0
        else:
            # Fallback to CLI
            run_mode = "cli"

    # Run in appropriate mode
    if run_mode == "gui":
        # GUI mode
        app = GitHubRepoSetup()
        app.run_gui()
    elif run_mode == "cli":
        # Command line mode
        folder = args.folder
        if not folder:
            folder = prompt_for_folder_cli()
        if not folder or not os.path.isdir(folder):
            print("❌ Error: Please specify a valid folder path for CLI mode.")
            print("Usage: python GitHubRepoSetup.py /path/to/folder")
            return 1
        
        visibility = "private" if args.private else "public"
        push = not args.no_push
        success = run_command_line(folder, visibility, args.description, push)
        return 0 if success else 1
    else:
        return 0

if __name__ == "__main__":
    sys.exit(main())
