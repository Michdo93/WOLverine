FROM python:3.8-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
        sqlite3 \
        libsqlite3-dev \
        gcc \
        build-essential \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /WOLverine

# Copy project files into container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Initializing the app
RUN python3 /WOLverine/create_db.py
RUN mkdir -p /app/defaults
RUN cp /WOLverine/instance/wolverine.db /app/defaults/wolverine.db

# Expose Flask port
EXPOSE 5000

# Run the application
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
