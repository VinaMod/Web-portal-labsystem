FROM php:8.0-apache
RUN docker-php-ext-install mysqli pdo pdo_mysql

# Set working directory
WORKDIR /var/www/html

# Copy source code into image (ephemeral - no host mount)
COPY src/ /var/www/html/

# Copy custom entrypoint
COPY docker-entrypoint-web.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint-web.sh

RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 777 /var/www/html

ENTRYPOINT ["docker-entrypoint-web.sh"]
