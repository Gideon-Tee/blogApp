FROM python:3.9-alpine

# Set the working directory
WORKDIR /app

# Copy Requirements
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose the port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]