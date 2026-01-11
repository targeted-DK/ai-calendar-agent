#!/bin/bash
set -e

# Export environment variables for cron
printenv | grep -v "no_proxy" >> /etc/environment

# Wait for PostgreSQL to be ready
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for PostgreSQL..."

    # Extract host and port from DATABASE_URL
    # Format: postgresql://user:password@host:port/dbname
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -q; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 2
    done

    echo "PostgreSQL is ready!"
fi

# Handle different commands
case "$1" in
    cron)
        echo "Starting cron daemon..."
        cron -f
        ;;
    init-db)
        echo "Initializing database..."
        python database/init_db.py
        ;;
    plan)
        echo "Running workout planner..."
        shift
        python scripts/plan_workouts.py "$@"
        ;;
    reconcile)
        echo "Running reconciliation..."
        shift
        python scripts/reconcile_workouts.py "$@"
        ;;
    import-garmin)
        echo "Importing Garmin data..."
        shift
        python scripts/import_garmin_data.py "$@"
        ;;
    import-calendar)
        echo "Importing calendar events..."
        shift
        python scripts/import_calendar_events.py "$@"
        ;;
    run-all)
        echo "Running full import pipeline..."
        python scripts/import_garmin_data.py --days=3
        python scripts/reconcile_workouts.py --days=7
        python scripts/import_calendar_events.py --past 7 --future 90
        python scripts/plan_workouts.py --days=3
        ;;
    test)
        echo "Running tests..."
        pytest tests/ -v
        ;;
    auth-calendar)
        echo "Starting Google Calendar authentication..."
        echo "NOTE: This requires browser access. Run with -it flag."
        python scripts/test_calendar.py
        ;;
    shell)
        exec /bin/bash
        ;;
    *)
        exec "$@"
        ;;
esac
