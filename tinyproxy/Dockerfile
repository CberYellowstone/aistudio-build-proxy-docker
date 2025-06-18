# Use a lightweight base image
FROM alpine:latest

# Install tinyproxy, dos2unix and netcat for health checks
RUN apk --no-cache add tinyproxy dos2unix netcat-openbsd

# The tinyproxy package creates the user and group automatically.
# We only need to create and set permissions for the log directory.
RUN mkdir -p /var/log/tinyproxy && \
    chown -R tinyproxy:tinyproxy /var/log/tinyproxy

# Copy the configuration template and entrypoint script
COPY tinyproxy.conf.template /etc/tinyproxy/tinyproxy.conf.template
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

# Convert line endings from CRLF (Windows) to LF (Unix)
RUN dos2unix /etc/tinyproxy/tinyproxy.conf.template
RUN dos2unix /usr/local/bin/entrypoint.sh

# Make the entrypoint script executable
RUN chmod +x /usr/local/bin/entrypoint.sh

# Expose the proxy port
EXPOSE 8888

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]