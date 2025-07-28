# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TERM=xterm-256color

# Install system dependencies for terminal support
RUN apt-get update && apt-get install -y \
    curl \
    less \
    nano \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY tui_requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r tui_requirements.txt

# Copy the TUI client code
COPY tui_client.py /app/

# Make the script executable
RUN chmod +x tui_client.py

# Set default API endpoint (can be overridden at runtime)
ENV API_BASE_URL=http://localhost:8000

# Create a simple entrypoint script
RUN echo '#!/bin/bash\n\
echo "Gemini Web Wrapper TUI Client"\n\
echo "Connecting to API at: ${API_BASE_URL:-http://localhost:8000}"\n\
echo "Press Ctrl+C to exit"\n\
echo ""\n\
exec python3 tui_client.py "$@"' > /app/entrypoint.sh && \
chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (can be overridden)
CMD []