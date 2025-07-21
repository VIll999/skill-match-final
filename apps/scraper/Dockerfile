FROM python:3.11-slim

# Install system dependencies including cron
RUN apt-get update && apt-get install -y \
    cron \
    wget \
    gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Create log directory
RUN mkdir -p /var/log && chmod 755 /var/log

# Create non-root user but keep root for cron
RUN useradd -m -u 1000 scraper && chown -R scraper:scraper /app

# Make cron_scraper.py executable
RUN chmod +x ./src/cron_scraper.py

# Default command (runs cron with daily job at 2 AM)
CMD ["sh", "-c", "echo '0 2 * * * cd /app && python src/cron_scraper.py >> /var/log/daily_job_scraper.log 2>&1' | crontab - && cron && tail -f /var/log/daily_job_scraper.log"]