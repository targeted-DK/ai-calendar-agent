# Auto Git - Automatic Commit & Push Guide

Automatically commits and pushes changes to GitHub when you work on your project.

## How It Works

The `auto_git.py` script:
1. **Watches** your project directory for file changes
2. **Waits** until a minimum number of files have changed (default: 3)
3. **Auto-commits** with intelligent commit messages
4. **Auto-pushes** to GitHub
5. **Repeats** every 5 minutes (configurable)

## Quick Start

### Option 1: Run in Terminal (Simple)

Open a terminal and run:
```bash
cd /home/targeteer/ai-calendar-agent
python auto_git.py
```

Keep this terminal open. Press `Ctrl+C` to stop.

### Option 2: Run in Background (Advanced)

Run in background with `nohup`:
```bash
cd /home/targeteer/ai-calendar-agent
nohup python auto_git.py > auto_git.log 2>&1 &
```

To stop it:
```bash
pkill -f auto_git.py
```

### Option 3: Run on Startup (Advanced)

Create a systemd service to run automatically on boot.

## Configuration

### Basic Settings (Edit the script)

Open `auto_git.py` and modify these variables:
```python
check_interval = 300  # Seconds between checks (300 = 5 minutes)
min_changes = 3       # Minimum files changed to trigger commit
```

### Command Line Arguments

You can also configure via command line:
```bash
python auto_git.py [check_interval] [min_changes]
```

Examples:
```bash
# Check every 3 minutes, commit at 2+ changes
python auto_git.py 180 2

# Check every 10 minutes, commit at 5+ changes
python auto_git.py 600 5

# Check every minute, commit at 1 change (aggressive)
python auto_git.py 60 1
```

## Smart Commit Messages

The script generates intelligent commit messages based on what changed:

**Example 1:** Changed 3 Python files
```
Auto-commit: Update code (3 files)

Changed files:
- agents/scheduler_agent.py
- tools/calendar_tools.py
- main.py

🤖 Automated commit by auto_git.py
```

**Example 2:** Changed code and docs
```
Auto-commit: Update code (2 files), Update docs (1 files)

🤖 Automated commit by auto_git.py
```

**Example 3:** Many files changed
```
Auto-commit: Update 15 files

🤖 Automated commit by auto_git.py
```

## Multiple Projects

To watch multiple projects, run separate instances:

**Terminal 1:**
```bash
cd /home/targeteer/ai-calendar-agent
python auto_git.py
```

**Terminal 2:**
```bash
cd /home/targeteer/another-project
python /home/targeteer/ai-calendar-agent/auto_git.py
```

Or copy `auto_git.py` to each project.

## Systemd Service (Auto-start on Boot)

Create a systemd service to run automatically:

**1. Create service file:**
```bash
sudo nano /etc/systemd/system/auto-git-calendar.service
```

**2. Add this content:**
```ini
[Unit]
Description=Auto Git for AI Calendar Agent
After=network.target

[Service]
Type=simple
User=targeteer
WorkingDirectory=/home/targeteer/ai-calendar-agent
ExecStart=/usr/bin/python3 /home/targeteer/ai-calendar-agent/auto_git.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**3. Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable auto-git-calendar
sudo systemctl start auto-git-calendar
```

**4. Check status:**
```bash
sudo systemctl status auto-git-calendar
```

**5. View logs:**
```bash
sudo journalctl -u auto-git-calendar -f
```

## Tips & Best Practices

### When to Use Auto Git

✅ **Good for:**
- Active development sessions
- Ensuring work is backed up regularly
- Solo projects where commit quality is less critical
- Prototyping and experimentation

❌ **Not ideal for:**
- Team projects (can create messy history)
- When you need precise, meaningful commits
- Projects requiring code review before commit

### Recommended Settings

**For active development:**
```bash
python auto_git.py 180 2  # Every 3 minutes, 2+ changes
```

**For periodic backups:**
```bash
python auto_git.py 600 5  # Every 10 minutes, 5+ changes
```

**For aggressive auto-save:**
```bash
python auto_git.py 60 1   # Every minute, any change
```

### Combining with Manual Commits

You can still make manual commits! Auto Git only commits when:
1. Changes are detected
2. You haven't manually committed recently

Best practice: Make important commits manually, let Auto Git handle backups.

## Troubleshooting

### Script won't start
```bash
# Check if it's already running
ps aux | grep auto_git.py

# Kill existing instance
pkill -f auto_git.py
```

### No commits happening
- Check if you have enough changed files (default: 3)
- Lower `min_changes`: `python auto_git.py 300 1`
- Check if files are in `.gitignore`

### Push failures
- Ensure SSH key is set up correctly
- Test manual push: `git push`
- Check internet connection

### Too many commits
- Increase `check_interval`: `python auto_git.py 600 3`
- Increase `min_changes`: `python auto_git.py 300 10`

## Stopping Auto Git

**If running in foreground:**
```bash
Ctrl+C
```

**If running in background:**
```bash
pkill -f auto_git.py
```

**If using systemd:**
```bash
sudo systemctl stop auto-git-calendar
```

## Viewing Activity

**Check what's running:**
```bash
ps aux | grep auto_git.py
```

**View recent commits:**
```bash
git log --oneline -10
```

**See what would be committed:**
```bash
git status
```

## Security Notes

- Auto Git uses your existing git credentials (SSH key)
- No passwords or tokens are stored in the script
- Only commits to repositories you already have push access to
- Respects `.gitignore` (won't commit ignored files)

## Customization

You can modify `auto_git.py` to:
- Change commit message format
- Add more file categorization
- Filter certain file types
- Add notifications (email, Slack, etc.)
- Run pre-commit hooks

## Examples

### Development Session Example

```bash
# Start Auto Git
python auto_git.py 180 2

# Work on your code...
# Edit agents/scheduler_agent.py
# Edit tools/calendar_tools.py

# After 3 minutes, Auto Git commits and pushes
# Continue working...
# Edit main.py
# Edit config/settings.py

# After 3 more minutes, another auto-commit
```

### Multi-Project Setup

Create a startup script:
```bash
#!/bin/bash
# auto_git_all.sh

cd /home/targeteer/ai-calendar-agent
python auto_git.py 300 3 > ~/logs/calendar-agent.log 2>&1 &

cd /home/targeteer/another-project
python /path/to/auto_git.py 300 3 > ~/logs/another-project.log 2>&1 &
```

## FAQ

**Q: Will this commit half-finished code?**
A: Yes. It commits whatever changes exist. Use manual commits for important milestones.

**Q: Can I pause it temporarily?**
A: Yes, press `Ctrl+C` or `pkill -f auto_git.py`, then restart when ready.

**Q: Does it work with private repos?**
A: Yes, as long as you have push access (SSH key configured).

**Q: What if I'm offline?**
A: Commits will succeed locally but push will fail. They'll push next time you're online.

**Q: Can I use this with multiple branches?**
A: Yes, it commits to whatever branch you currently have checked out.
