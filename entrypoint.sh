#!/bin/bash
DB_PATH="/WOLverine/instance/wolverine.db"
TEMPLATE_PATH="/app/defaults/wolverine.db"

if [ ! -f "$DB_PATH" ]; then
    echo "Database not found - copy default DB..."
    cp "$TEMPLATE_PATH" "$DB_PATH"
fi

exec python3 app.py
