# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 5000 and set default port environment variable
ENV PORT=5000
EXPOSE 5000

# Run the application with gunicorn, honoring the PORT environment variable
CMD ["sh", "-c", "gunicorn -w 3 -k gthread --threads 4 -b 0.0.0.0:${PORT} app:app"]
