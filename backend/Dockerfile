# Use a lightweight Python image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy backend requirements file and install dependencies
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt

# Copy the backend code
COPY backend ./backend

# Copy config files
COPY config ./config

# Copy model predictions for inference
COPY src/results/predictions ./src/results/predictions

# Expose the port your backend runs on (8000)
EXPOSE 8000

# Command to run the backend
# API will listen on 0.0.0.0:8000 inside container (configured via HOST env var)
CMD ["python", "-m", "backend.api_server"]