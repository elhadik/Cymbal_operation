FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run sets the PORT environment variable
ENV PORT=8080

# Run the application
CMD ["python", "app.py"]
