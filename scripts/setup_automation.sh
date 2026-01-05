#!/bin/bash
# Setup script for daily automation
# Choose between cron or systemd

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_DIR/venv"

echo "=================================="
echo "AI Calendar Agent - Automation Setup"
echo "=================================="
echo ""
echo "Choose automation method:"
echo "1) Cron Job (simple, runs at specific time)"
echo "2) Systemd Timer (recommended for production)"
echo "3) Manual only (no automation)"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "Setting up Cron Job..."
        echo ""

        # Make script executable
        chmod +x "$SCRIPT_DIR/daily_automation.py"

        # Create wrapper script that activates venv
        WRAPPER_SCRIPT="$SCRIPT_DIR/run_daily_automation.sh"
        cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash
source "$VENV_PATH/bin/activate"
cd "$PROJECT_DIR"
python "$SCRIPT_DIR/daily_automation.py"
EOF
        chmod +x "$WRAPPER_SCRIPT"

        echo "Cron job command (runs every 30 minutes):"
        echo ""
        echo "*/30 * * * * $WRAPPER_SCRIPT >> $HOME/.local/share/ai-calendar-agent/automation.log 2>&1"
        echo ""
        echo "To install, run:"
        echo "  crontab -e"
        echo ""
        echo "Then add the line above."
        echo ""
        echo "Alternative schedules:"
        echo "  Every 15 minutes: */15 * * * * $WRAPPER_SCRIPT >> ..."
        echo "  Every hour:       0 * * * * $WRAPPER_SCRIPT >> ..."
        echo "  Daily at 6 AM:    0 6 * * * $WRAPPER_SCRIPT >> ..."
        ;;

    2)
        echo ""
        echo "Setting up Systemd Timer..."
        echo ""

        # Make script executable
        chmod +x "$SCRIPT_DIR/daily_automation.py"

        # Create systemd service file
        SERVICE_FILE="$HOME/.config/systemd/user/ai-calendar-automation.service"
        mkdir -p "$HOME/.config/systemd/user"

        cat > "$SERVICE_FILE" << EOF
[Unit]
Description=AI Calendar Agent Daily Automation
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_PATH/bin/python $SCRIPT_DIR/daily_automation.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

        # Create systemd timer file (runs daily at 6:00 AM)
        TIMER_FILE="$HOME/.config/systemd/user/ai-calendar-automation.timer"

        # Ask for frequency
        echo ""
        echo "Select run frequency:"
        echo "1) Every 30 minutes (recommended for active monitoring)"
        echo "2) Every hour"
        echo "3) Daily at 6 AM"
        echo ""
        read -p "Enter choice [1-3]: " freq_choice

        case $freq_choice in
            1)
                TIMER_INTERVAL="*:00/30"  # Every 30 minutes
                TIMER_DESC="every 30 minutes"
                ;;
            2)
                TIMER_INTERVAL="*:00:00"  # Every hour
                TIMER_DESC="hourly"
                ;;
            3)
                TIMER_INTERVAL="*-*-* 06:00:00"  # Daily at 6 AM
                TIMER_DESC="daily at 6:00 AM"
                ;;
            *)
                TIMER_INTERVAL="*:00/30"  # Default to 30 minutes
                TIMER_DESC="every 30 minutes (default)"
                ;;
        esac

        cat > "$TIMER_FILE" << EOF
[Unit]
Description=Run AI Calendar Automation $TIMER_DESC
Requires=ai-calendar-automation.service

[Timer]
# Run $TIMER_DESC
OnCalendar=$TIMER_INTERVAL
# Run on boot if we missed a scheduled run
Persistent=true
# Small random delay to avoid exact-time server load
RandomizedDelaySec=60

[Install]
WantedBy=timers.target
EOF

        # Enable and start the timer
        systemctl --user daemon-reload
        systemctl --user enable ai-calendar-automation.timer
        systemctl --user start ai-calendar-automation.timer

        echo "✅ Systemd timer installed (running $TIMER_DESC)!"
        echo ""
        echo "Check status:"
        echo "  systemctl --user status ai-calendar-automation.timer"
        echo ""
        echo "View logs:"
        echo "  journalctl --user -u ai-calendar-automation.service -f"
        echo ""
        echo "Run manually:"
        echo "  systemctl --user start ai-calendar-automation.service"
        echo ""
        echo "Disable automation:"
        echo "  systemctl --user stop ai-calendar-automation.timer"
        echo "  systemctl --user disable ai-calendar-automation.timer"
        ;;

    3)
        echo ""
        echo "Manual mode selected. Run automation manually:"
        echo "  python scripts/daily_automation.py"
        echo ""
        ;;

    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
