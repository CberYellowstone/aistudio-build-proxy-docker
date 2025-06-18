#!/bin/sh
set -e

CONF_TEMPLATE="/etc/tinyproxy/tinyproxy.conf.template"
CONF_FILE="/etc/tinyproxy/tinyproxy.conf"

# Create the final config from the template
cp "$CONF_TEMPLATE" "$CONF_FILE"

# Check if upstream SOCKS server is configured and append it to the config file
if [ -n "$UPSTREAM_SOCKS_SERVER" ] && [ -n "$UPSTREAM_SOCKS_PORT" ]; then
    echo "Configuring upstream SOCKS5 proxy..."
    
    # Base upstream string
    UPSTREAM_STR="upstream socks5"
    
    # Add user and password if they exist
    if [ -n "$UPSTREAM_SOCKS_USER" ] && [ -n "$UPSTREAM_SOCKS_PASS" ]; then
        UPSTREAM_STR="$UPSTREAM_STR $UPSTREAM_SOCKS_USER:$UPSTREAM_SOCKS_PASS@$UPSTREAM_SOCKS_SERVER:$UPSTREAM_SOCKS_PORT"
    else
        UPSTREAM_STR="$UPSTREAM_STR $UPSTREAM_SOCKS_SERVER:$UPSTREAM_SOCKS_PORT"
    fi
    
    # Append the correctly formatted line to the config file, ensuring it's on a new line.
    echo "" >> "$CONF_FILE" # Add a newline for safety
    echo "$UPSTREAM_STR" >> "$CONF_FILE"
    echo "Upstream proxy configured."
else
    echo "No upstream SOCKS5 proxy configured. Tinyproxy will act as a direct proxy."
fi

# Make sure the log file exists and has correct permissions
touch /var/log/tinyproxy/tinyproxy.log
chown tinyproxy:tinyproxy /var/log/tinyproxy/tinyproxy.log

# Start tinyproxy in the foreground
exec tinyproxy -d