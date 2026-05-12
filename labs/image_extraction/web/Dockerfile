FROM php:8.2-apache

# Enable mod_rewrite if needed
RUN a2enmod rewrite

# Install exiftool if wanted in container for students (optional, but good for the lab)
RUN apt-get update && apt-get install -y libimage-exiftool-perl && rm -rf /var/lib/apt/lists/*

# Copy web files
COPY . /var/www/html/

# Set permissions
RUN chown -R www-data:www-data /var/www/html

# Use entrypoint
RUN chmod +x /var/www/html/entrypoint.sh
ENTRYPOINT ["/var/www/html/entrypoint.sh"]
