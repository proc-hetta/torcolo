FROM python:3.13

# Create unprivileged user
RUN useradd -s /bin/false torcolo

# Setup working directory
RUN mkdir -p /app && chown torcolo:torcolo /app
WORKDIR /app

# Setup database directory
RUN mkdir /app/torcolodb && chown torcolo:torcolo /app/torcolodb

# Copy all files in directory
COPY --chown=torcolo . ./

# Install dependencies
RUN python3 -m pip install -r requirements.txt

# Run web application
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
