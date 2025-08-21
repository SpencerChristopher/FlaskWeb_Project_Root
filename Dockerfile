# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
# Since we are using pyproject.toml, we will install poetry and then dependencies
RUN pip install poetry && poetry install --no-root

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run the application
CMD ["poetry", "run", "gunicorn", "--bind", "0.0.0.0:5000", "app:wsgi_app"]