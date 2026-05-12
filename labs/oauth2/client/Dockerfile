FROM php:8.1-apache

RUN a2enmod rewrite

COPY src/ /var/www/html/
RUN chown -R www-data:www-data /var/www/html

# Install curl for API calls
RUN apt-get update && apt-get install -y libcurl4-openssl-dev pkg-config libssl-dev \
    && docker-php-ext-install curl
