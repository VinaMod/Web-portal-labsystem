FROM php:8.2-apache

# Install dependencies for flag generation
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy site files
COPY . /var/www/html/

# Set permissions
RUN chown -R www-data:www-data /var/www/html && \
    chmod +x /var/www/html/entrypoint.sh

# Use the custom entrypoint for flag generation
ENTRYPOINT ["/var/www/html/entrypoint.sh"]
