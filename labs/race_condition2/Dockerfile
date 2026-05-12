FROM php:8.0-apache

# Cài PHP extension (thay cho command trong compose)
RUN docker-php-ext-install pdo pdo_mysql

# Copy source code vào image
COPY src/ /var/www/html/

# Fix permission triệt để tránh 403 Forbidden
RUN chown -R www-data:www-data /var/www/html \
 && chmod -R 755 /var/www/html

# Apache dùng port 80
EXPOSE 80
