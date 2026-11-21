FROM python:3.11-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./src .

# The configurations (config/README.md): without RPP_CONFIG_FILE the proxy reads /config/environments/epp-docker.yaml,
# the config/ tree next to src/, which is /app here
COPY config /config

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "uvicorn", "--host", "0.0.0.0", "--port", "8091", "main:app"]