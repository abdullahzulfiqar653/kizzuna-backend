# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create a non-root user and group
RUN groupadd -r myuser && useradd --no-log-init -r -g myuser -m myuser

# Update PATH environment variable to include the user-specific Python bin directory
ENV PATH=/home/myuser/.local/bin:$PATH

# Set the working directory in the container
WORKDIR /app

# Change the ownership of the /app directory to the non-root user
RUN chown -R myuser:myuser /app

# Install system dependencies
RUN apt update && \
    apt install -y default-mysql-client \ 
        default-libmysqlclient-dev \ 
        gcc \ 
        ffmpeg \ 
        curl \
        # Playwright dependencies
        libglib2.0-0 \               
        libnss3 \                                     
        libnspr4 \                                    
        libdbus-1-3 \                                 
        libatk1.0-0 \                                 
        libatk-bridge2.0-0 \                          
        libcups2 \                                    
        libatspi2.0-0 \                               
        libx11-6 \                                    
        libxcomposite1 \                              
        libxdamage1 \                                 
        libxext6 \                                    
        libxfixes3 \                                  
        libxrandr2 \                                  
        libgbm1 \                                     
        libdrm2 \                                     
        libxcb1 \                                     
        libxkbcommon0 \                               
        libpango-1.0-0 \                              
        libcairo2 \                                   
        libasound2     

# Switch to the non-root user
USER myuser

# Copy the current directory contents into the container at /app
COPY --chown=myuser:myuser ./requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install -U pip && \
    pip install --user --no-cache-dir -r requirements.txt

RUN playwright install chromium && \
    # playwright install-deps && \
    python -m nltk.downloader punkt

# Copy source code
COPY --chown=myuser:myuser . /app/

# Expose port 8000 for the Django development server
EXPOSE 8000

CMD ["bash", "docker-entrypoint.sh"]
