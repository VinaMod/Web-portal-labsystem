FROM php:8.1-apache

# Cài đặt MySQL Server và các packages cần thiết
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    zip \
    unzip \
    git \
    cron \
    default-mysql-server \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt các extension PHP cần thiết
RUN docker-php-ext-install pdo pdo_mysql mysqli

# Enable Apache modules
RUN a2enmod rewrite

# Set working directory
WORKDIR /var/www/html

# Copy source code into image (ephemeral - no host mount)
COPY src/ /var/www/html/

# Copy config files
COPY config/php.ini /usr/local/etc/php/php.ini
COPY config/mysql.cnf /etc/mysql/conf.d/custom.cnf

# Copy database init script
COPY database/init.sql /docker-entrypoint-initdb.d/init.sql

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create log directory and files with proper permissions
RUN mkdir -p /var/log \
    && touch /var/log/sqli_attempts.log \
    && chmod 666 /var/log/sqli_attempts.log \
    && chown www-data:www-data /var/log/sqli_attempts.log

# Create MySQL directories with proper permissions
RUN mkdir -p /var/run/mysqld /var/log/mysql \
    && touch /var/log/mysql/error.log \
    && chmod 777 /var/log/mysql/error.log \
    && chown -R mysql:mysql /var/run/mysqld /var/log/mysql

# Set proper permissions for web directory (777 for MySQL INTO OUTFILE)
RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 777 /var/www/html

# Expose ports (80 for Apache, 3306 for MySQL)
EXPOSE 80 3306

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
