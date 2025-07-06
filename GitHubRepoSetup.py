#!/usr/bin/env python3
"""
GitHub Repository Setup Tool
A tool to easily create and manage GitHub repositories from local folders.
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import git
from datetime import datetime
import argparse
import threading
import time
from typing import Optional

class GitHubRepoSetup:
    def __init__(self):
        self.root: Optional[tk.Tk] = None
        self.folder_var: Optional[tk.StringVar] = None
        self.status_label: Optional[tk.Label] = None
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.visibility_var: Optional[tk.StringVar] = None
        self.description_var: Optional[tk.StringVar] = None
        
    def get_git_status(self, path):
        """Get detailed Git status for a path"""
        if not path or not os.path.isdir(path):
            return "⚠️ Please select a valid folder."
            
        try:
            repo = git.Repo(path)
            last_commit = datetime.fromtimestamp(repo.head.commit.committed_date).strftime('%Y-%m-%d %H:%M:%S')
            remote_url = next(repo.remote().urls) if repo.remotes else "No remote configured"
            branch = repo.active_branch.name
            return f"✅ Git repository found\n📅 Last commit: {last_commit}\n🌐 Remote: {remote_url}\n🌿 Branch: {branch}"
        except git.exc.InvalidGitRepositoryError:
            return "⚠️ Not a Git repository.\n💡 Click 'Initialize Git' to start."
        except Exception as e:
            return f"⚠️ Git error: {str(e)}"

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
        if not self.folder_var or not self.status_label:
            return
        status = self.get_git_status(self.folder_var.get())
        self.status_label.config(text=status)

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
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(4, weight=1)

        # Style
        style = ttk.Style()
        style.theme_use('clam')

        # Title
        title_label = tk.Label(self.root, text="GitHub Repository Setup", 
                             font=("Arial", 16, "bold"), fg="#2c3e50")
        title_label.grid(row=0, column=0, pady=10)

        # Folder selection
        folder_frame = ttk.LabelFrame(self.root, text="Project Folder", padding=10)
        folder_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        folder_frame.grid_columnconfigure(0, weight=1)

        self.folder_var = tk.StringVar()
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, width=50)
        folder_entry.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        browse_btn = ttk.Button(folder_frame, text="Browse", command=self.browse_folder)
        browse_btn.grid(row=0, column=1)

        # Repository options
        options_frame = ttk.LabelFrame(self.root, text="Repository Options", padding=10)
        options_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        options_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(options_frame, text="Visibility:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.visibility_var = tk.StringVar(value="Public")
        visibility_combo = ttk.Combobox(options_frame, textvariable=self.visibility_var, 
                                      values=["Public", "Private"], state="readonly", width=15)
        visibility_combo.grid(row=0, column=1, sticky="w")

        ttk.Label(options_frame, text="Description:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=(10, 0))
        self.description_var = tk.StringVar()
        description_entry = ttk.Entry(options_frame, textvariable=self.description_var, width=40)
        description_entry.grid(row=1, column=1, sticky="ew", pady=(10, 0))

        # Action buttons
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=3, column=0, pady=10)
        
        init_btn = ttk.Button(button_frame, text="Initialize Git", command=self.initialize_git)
        init_btn.pack(side=tk.LEFT, padx=5)
        
        create_btn = ttk.Button(button_frame, text="Create & Push to GitHub", 
                               command=self.create_or_push_repo)
        create_btn.pack(side=tk.LEFT, padx=5)
        
        explorer_btn = ttk.Button(button_frame, text="Open Folder", command=self.open_in_explorer)
        explorer_btn.pack(side=tk.LEFT, padx=5)
        
        github_btn = ttk.Button(button_frame, text="Open in GitHub", command=self.open_in_github)
        github_btn.pack(side=tk.LEFT, padx=5)

        # Progress bar
        self.progress_bar = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress_bar.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        # Status display
        status_frame = ttk.LabelFrame(self.root, text="Status", padding=10)
        status_frame.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = tk.Label(status_frame, text="No folder selected.", 
                                   justify=tk.LEFT, wraplength=550)
        self.status_label.grid(row=0, column=0, sticky="ew")

        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Browse Folder", command=self.browse_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=lambda: self.root.quit() if self.root else None)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

        # Keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.browse_folder())
        self.root.bind('<Control-q>', lambda e: self.root.quit() if self.root else None)
        self.root.bind('<Escape>', lambda e: self.root.quit() if self.root else None)

    def show_about(self):
        """Show about dialog"""
        about_text = """GitHub Repository Setup Tool v1.0

A simple tool to create and manage GitHub repositories.

Features:
• Initialize Git repositories
• Create GitHub repositories
• Push code to GitHub
• Manage repository visibility and description

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
    """Run the tool from command line"""
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return False

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
        print(f"🚀 Creating GitHub repository '{repo_name}'...")
        
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

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="GitHub Repository Setup Tool")
    parser.add_argument("folder", nargs="?", help="Folder path to setup as GitHub repository")
    parser.add_argument("--private", action="store_true", help="Create private repository (default: public)")
    parser.add_argument("--description", "-d", help="Repository description")
    parser.add_argument("--no-push", action="store_true", help="Don't push code after creation")
    parser.add_argument("--gui", action="store_true", help="Launch GUI mode")
    
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

    # Run in appropriate mode
    if args.gui or not args.folder:
        # GUI mode
        app = GitHubRepoSetup()
        app.run_gui()
    else:
        # Command line mode
        visibility = "private" if args.private else "public"
        push = not args.no_push
        success = run_command_line(args.folder, visibility, args.description, push)
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
