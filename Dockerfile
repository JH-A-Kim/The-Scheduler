# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Install required C++11 libraries and ca-certificates
# Must Use a subdomain
RUN apt-get update \
      \
      && apt-get install -y \
          --no-install-recommends \
            build-essential \
            python3-dev \
            ca-certificates \
            curl \
            libopencv-dev \
            python3-opencv \
      && rm -rf /var/lib/apt/lists/*

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 5000 available to the world outside this container
EXPOSE 5001

# Run main when the container launches
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:5001", "main:app"]
USER nobody