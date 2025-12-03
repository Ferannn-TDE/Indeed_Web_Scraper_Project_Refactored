# Use an official lightweight Python image
FROM python:3.12-slim

# Avoid interactive prompts during package installs
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

# Set working directory inside the container
WORKDIR /app

# Install system dependencies (for pdfplumber, sentence-transformers, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the image
COPY . .

# Default environment variables (you can override at runtime)
# e.g. docker run -e JSEARCH_API_KEY=your_key ...
ENV JSEARCH_API_KEY=""

# Default command:
# - run tests by default so the container is CI-friendly
# You can override this CMD to run the app instead.
#CMD ["python", "-m", "unittest", "test_app.py"]

#CMD ["python", "main.py"]
CMD ["pytest", "-q"]

# to run in terminal:
# docker run --rm resume-job-matcher python -m unittest test_app.py
