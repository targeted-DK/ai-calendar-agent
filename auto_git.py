#!/usr/bin/env python3
"""
Auto Git - Automatic commit and push script
Watches for file changes and automatically commits & pushes to GitHub
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path


class AutoGit:
    def __init__(self, repo_path, check_interval=300, min_changes=3):
        """
        Initialize AutoGit.

        Args:
            repo_path: Path to git repository
            check_interval: Seconds between checks (default: 300 = 5 minutes)
            min_changes: Minimum number of changed files to trigger commit (default: 3)
        """
        self.repo_path = Path(repo_path).resolve()
        self.check_interval = check_interval
        self.min_changes = min_changes

        if not (self.repo_path / '.git').exists():
            raise ValueError(f"{repo_path} is not a git repository")

    def run_git_command(self, *args):
        """Run a git command and return output."""
        try:
            result = subprocess.run(
                ['git', '-C', str(self.repo_path)] + list(args),
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git error: {e.stderr}")
            return None

    def get_changed_files(self):
        """Get list of changed files."""
        # Get untracked files
        untracked = self.run_git_command('ls-files', '--others', '--exclude-standard')
        untracked_files = untracked.split('\n') if untracked else []

        # Get modified files
        modified = self.run_git_command('diff', '--name-only')
        modified_files = modified.split('\n') if modified else []

        # Combine and filter empty strings
        all_changes = [f for f in untracked_files + modified_files if f]

        return all_changes

    def generate_commit_message(self, changed_files):
        """Generate an intelligent commit message based on changed files."""
        if not changed_files:
            return "Auto-commit: Minor updates"

        # Categorize changes
        categories = {
            'code': ['.py', '.js', '.ts', '.java', '.go', '.rs'],
            'config': ['.json', '.yaml', '.yml', '.toml', '.env.example'],
            'docs': ['.md', '.txt', '.rst'],
            'tests': ['test_', '_test.py', '.test.js'],
            'data': ['.csv', '.json', '.xml'],
        }

        changes_by_type = {}
        for file in changed_files:
            file_lower = file.lower()
            categorized = False

            for category, extensions in categories.items():
                if any(file_lower.endswith(ext) or ext in file_lower for ext in extensions):
                    changes_by_type[category] = changes_by_type.get(category, 0) + 1
                    categorized = True
                    break

            if not categorized:
                changes_by_type['other'] = changes_by_type.get('other', 0) + 1

        # Build commit message
        parts = []
        if changes_by_type.get('code', 0) > 0:
            parts.append(f"Update code ({changes_by_type['code']} files)")
        if changes_by_type.get('docs', 0) > 0:
            parts.append(f"Update docs ({changes_by_type['docs']} files)")
        if changes_by_type.get('config', 0) > 0:
            parts.append(f"Update config ({changes_by_type['config']} files)")
        if changes_by_type.get('tests', 0) > 0:
            parts.append(f"Update tests ({changes_by_type['tests']} files)")

        if not parts:
            parts = [f"Update {len(changed_files)} files"]

        message = "Auto-commit: " + ", ".join(parts)

        # Add file list if small enough
        if len(changed_files) <= 5:
            file_list = "\n\nChanged files:\n" + "\n".join(f"- {f}" for f in changed_files)
            message += file_list

        message += "\n\n🤖 Automated commit by auto_git.py"

        return message

    def commit_and_push(self, changed_files):
        """Commit and push changes."""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
        print(f"Found {len(changed_files)} changed file(s)")

        # Add all changes
        print("Adding changes...")
        self.run_git_command('add', '.')

        # Generate commit message
        commit_msg = self.generate_commit_message(changed_files)
        print(f"Commit message:\n{commit_msg}\n")

        # Commit
        print("Committing...")
        self.run_git_command('commit', '-m', commit_msg)

        # Push
        print("Pushing to GitHub...")
        push_result = self.run_git_command('push')

        if push_result is not None:
            print("✅ Successfully pushed to GitHub!")
        else:
            print("❌ Failed to push to GitHub")

        print("-" * 60)

    def watch(self):
        """Watch for changes and auto-commit."""
        print("=" * 60)
        print("Auto Git - Automatic Commit & Push")
        print("=" * 60)
        print(f"Repository: {self.repo_path}")
        print(f"Check interval: {self.check_interval} seconds")
        print(f"Minimum changes to trigger: {min_changes}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print("\nWatching for changes... (Press Ctrl+C to stop)\n")

        try:
            while True:
                changed_files = self.get_changed_files()

                if len(changed_files) >= self.min_changes:
                    self.commit_and_push(changed_files)
                else:
                    if changed_files:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                              f"{len(changed_files)} file(s) changed (waiting for {self.min_changes})")

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n\n⏹️  Auto Git stopped by user")
            sys.exit(0)


if __name__ == "__main__":
    # Configuration
    repo_path = os.path.dirname(os.path.abspath(__file__))
    check_interval = 300  # 5 minutes
    min_changes = 3  # Minimum 3 changed files to trigger commit

    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("Usage: python auto_git.py [check_interval] [min_changes]")
            print("\nArguments:")
            print("  check_interval  Seconds between checks (default: 300)")
            print("  min_changes     Minimum files changed to commit (default: 3)")
            print("\nExample:")
            print("  python auto_git.py 180 2  # Check every 3 minutes, commit at 2+ changes")
            sys.exit(0)

        if len(sys.argv) > 1:
            check_interval = int(sys.argv[1])
        if len(sys.argv) > 2:
            min_changes = int(sys.argv[2])

    # Start watching
    auto_git = AutoGit(repo_path, check_interval, min_changes)
    auto_git.watch()
