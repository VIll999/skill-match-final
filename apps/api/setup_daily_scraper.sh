#!/bin/bash
"""
Setup daily job scraper cron job
"""

echo "🚀 Setting up Daily Job Scraper"
echo "================================"

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DAILY_SCRAPER="$SCRIPT_DIR/load_daily_jobs.py"

echo "Script location: $DAILY_SCRAPER"

# Check if the script exists
if [ ! -f "$DAILY_SCRAPER" ]; then
    echo "❌ Error: Daily scraper script not found at $DAILY_SCRAPER"
    exit 1
fi

# Make the script executable
chmod +x "$DAILY_SCRAPER"

# Create a wrapper script for cron (handles environment)
WRAPPER_SCRIPT="$SCRIPT_DIR/run_daily_scraper.sh"

cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash
# Daily job scraper wrapper for cron

# Set environment variables
export PATH="/usr/local/bin:/usr/bin:/bin"

# Change to script directory
cd "$SCRIPT_DIR"

# Load environment variables
source "/home/v999/Desktop/skill-match/secrets/.env.adzuna" 2>/dev/null || true

# Run the daily scraper
python3 "$DAILY_SCRAPER" --days 1 --mode append >> "/tmp/daily_job_scraper.log" 2>&1

# Log completion
echo "\$(date): Daily job scraper completed" >> "/tmp/daily_job_scraper.log"
EOF

chmod +x "$WRAPPER_SCRIPT"

echo "✅ Created wrapper script: $WRAPPER_SCRIPT"

# Show cron job options
echo ""
echo "📅 Cron Job Setup Options:"
echo "=========================="
echo ""
echo "1. Daily at 6 AM:"
echo "   0 6 * * * $WRAPPER_SCRIPT"
echo ""
echo "2. Daily at 2 AM:"
echo "   0 2 * * * $WRAPPER_SCRIPT"
echo ""
echo "3. Twice daily (6 AM and 6 PM):"
echo "   0 6,18 * * * $WRAPPER_SCRIPT"
echo ""
echo "4. Every 6 hours:"
echo "   0 */6 * * * $WRAPPER_SCRIPT"
echo ""

# Ask user which option they want
echo "Choose an option (1-4) or 'manual' to setup manually:"
read -r choice

case $choice in
    1)
        CRON_SCHEDULE="0 6 * * * $WRAPPER_SCRIPT"
        ;;
    2)
        CRON_SCHEDULE="0 2 * * * $WRAPPER_SCRIPT"
        ;;
    3)
        CRON_SCHEDULE="0 6,18 * * * $WRAPPER_SCRIPT"
        ;;
    4)
        CRON_SCHEDULE="0 */6 * * * $WRAPPER_SCRIPT"
        ;;
    manual)
        echo ""
        echo "Manual setup:"
        echo "1. Run: crontab -e"
        echo "2. Add this line:"
        echo "   0 6 * * * $WRAPPER_SCRIPT"
        echo "3. Save and exit"
        echo ""
        echo "Log file location: /tmp/daily_job_scraper.log"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Add to crontab
echo "Setting up cron job: $CRON_SCHEDULE"
(crontab -l 2>/dev/null; echo "$CRON_SCHEDULE") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Cron job added successfully!"
    echo ""
    echo "📋 Current crontab:"
    crontab -l | grep -E "(daily_scraper|load_daily_jobs)"
    echo ""
    echo "📄 Log file: /tmp/daily_job_scraper.log"
    echo ""
    echo "🧪 Test the scraper manually:"
    echo "   python3 $DAILY_SCRAPER --test"
    echo ""
    echo "🚀 Run the scraper now:"
    echo "   python3 $DAILY_SCRAPER --days 1"
else
    echo "❌ Failed to add cron job"
    exit 1
fi