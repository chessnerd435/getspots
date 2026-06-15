FROM python:3.11

# Set up the working directory
WORKDIR /app

# Copy all files from the current directory into the container
COPY . /app

# Install dependencies
RUN pip install -r requirements.txt

# Create a non-root user (required by Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Expose the port (Hugging Face dynamically assigns a port, which main.py uses via the PORT env variable)
EXPOSE 5050

# Start the server
CMD ["python", "main.py"]
