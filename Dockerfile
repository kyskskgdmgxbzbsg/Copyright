# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy files
COPY . .

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Run the bot
CMD ["python", "Copyright.py"]