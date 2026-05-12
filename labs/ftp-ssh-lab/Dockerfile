FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install required packages
RUN apt-get update && apt-get install -y \
    apache2 \
    php \
    libapache2-mod-php \
    vsftpd \
    openssh-server \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create dev01 user with home directory
RUN useradd -m -s /bin/bash dev01 && \
    echo "dev01:DevPassword123!" | chpasswd

# Create .ssh directory for dev01 (writable by everyone for exploit)
RUN mkdir -p /home/dev01/.ssh && \
    chmod 777 /home/dev01/.ssh && \
    chown dev01:dev01 /home/dev01/.ssh

# Create empty flag file (will be populated dynamically in entrypoint.sh)
RUN touch /home/dev01/flag.txt && \
    chmod 640 /home/dev01/flag.txt && \
    chown dev01:dev01 /home/dev01/flag.txt

# Create README file with username hint (readable by everyone)
RUN echo "This directory of dev01" > /home/dev01/README.txt && \
    chmod 644 /home/dev01/README.txt && \
    chown dev01:dev01 /home/dev01/README.txt

# Set /home/dev01 directory permissions (listable by everyone)
RUN chmod 755 /home/dev01 && \
    chown dev01:dev01 /home/dev01

# Configure SSH
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config && \
    sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config && \
    echo "PermitRootLogin no" >> /etc/ssh/sshd_config && \
    echo "StrictModes no" >> /etc/ssh/sshd_config

# Copy vsftpd configuration
COPY config/vsftpd.conf /etc/vsftpd.conf

# Copy web files
COPY web/ /var/www/html/
RUN chown -R www-data:www-data /var/www/html/

# Ensure ftp user is NOT in dev01 group (so it can't read the flag)
# This is already the case by default, but we verify it
# The ftp user should not be in dev01 group to prevent reading flag.txt (640 permissions)
RUN if id ftp 2>/dev/null | grep -q dev01; then echo "WARNING: ftp user is in dev01 group!"; exit 1; fi || true

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose ports
EXPOSE 80 21 22 20

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
