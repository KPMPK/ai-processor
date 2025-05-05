# Use an official Python image as the base
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Copy the application code into the container
COPY . /app

# Create a virtual environment (optional but recommended)
RUN python -m venv .venv

# Activate the virtual environment and install dependencies
RUN . .venv/bin/activate && pip install --upgrade pip \
    && pip install uvicorn \
    && pip install f5_ai_gateway_sdk-0.1.4.tar.gz

# Expose the application port
EXPOSE 9999

# Command to run the application
CMD [".venv/bin/python", "-m", "uvicorn", "patternred:app", "--host", "0.0.0.0", "--port", "9999", "--reload"]
