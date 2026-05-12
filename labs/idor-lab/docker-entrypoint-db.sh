#!/bin/bash
set -e

echo "🎲 IDOR Lab - Auto Random Data Generator"
echo "==========================================="

# Set timezone
export TZ=Asia/Ho_Chi_Minh

# Check if we need to generate new data
if [ ! -f /docker-entrypoint-initdb.d/init.sql ] || [ "$FORCE_REGENERATE" = "true" ]; then
    echo "📝 Generating random student data and FLAG locations..."
    
    cd /tmp
    
    # Copy generator script
    cp /setup/generate_sql.py /tmp/
    
    # Create sql directory
    mkdir -p /tmp/sql
    
    # Get current date in DDMMYYYY format (GMT+7)
    CURRENT_DATE=$(date +%d%m%Y)
    
    # Get email from env var
    EMAIL_VALUE=${EMAIL:-default@example.com}
    
    echo "📧 Email: $EMAIL_VALUE"
    echo "📅 Date: $CURRENT_DATE"
    
    # Determine IDOR mode (student_id or class_id)
    IDOR_MODE=${ENV:-student_id}
    echo "🎯 Mode: $IDOR_MODE"
    
    RANDOM_KEY=${RANDOM_KEY:-}
        
    # Run generator with email, date, and mode as arguments
    python3 generate_sql.py "$EMAIL_VALUE" "$CURRENT_DATE" "$IDOR_MODE" "$RANDOM_KEY"
    
    # Copy generated SQL to proper location
    cp /tmp/sql/init.sql /docker-entrypoint-initdb.d/init.sql
    
    echo "✅ Random data generated!"
else
    echo "ℹ️  Using existing data. Set FORCE_REGENERATE=true to regenerate."
fi

echo "🚀 Starting MySQL..."
echo ""

# Call original MySQL entrypoint
exec docker-entrypoint.sh "$@"
