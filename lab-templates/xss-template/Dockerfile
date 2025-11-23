FROM php:8.1-apache

# Cài đặt các extension PHP cần thiết
RUN docker-php-ext-install pdo pdo_mysql mysqli

# Bật mod_rewrite cho Apache
RUN a2enmod rewrite

# Cài đặt các package cần thiết
RUN apt-get update && apt-get install -y \
    libzip-dev \
    zip \
    unzip \
    cron \
    wget \
    gnupg \
    ca-certificates \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgtk-3-0 \
    libgbm1 \
    libasound2 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt extension zip
RUN docker-php-ext-install zip

# Cài đặt Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# Cài đặt Chromium (cho Puppeteer)
RUN apt-get update && \
    apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt Puppeteer
RUN npm install -g puppeteer-core

# Cấu hình Apache
RUN echo "ServerName localhost" >> /etc/apache2/apache2.conf

# Thêm cấu hình cho /var/www/html để bỏ qua .htaccess
RUN echo '<Directory /var/www/html>\n\
    Options Indexes FollowSymLinks\n\
    AllowOverride None\n\
    Require all granted\n\
</Directory>' > /etc/apache2/conf-available/custom.conf \
    && a2enconf custom

# Tạo thư mục log
RUN mkdir -p /var/log

# Script khởi động
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

COPY ./src/ /var/www/html/
RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html


# Khởi động Apache và monitor
CMD ["/usr/local/bin/docker-entrypoint.sh"]
