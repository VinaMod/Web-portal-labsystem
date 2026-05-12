FROM ubuntu:22.04

# Cài đặt Samba, OpenSSH Server và Nginx
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    samba \
    samba-common-bin \
    openssh-server \
    nginx \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Tạo thư mục SSH
RUN mkdir /var/run/sshd

# Tạo user SMB
RUN useradd -m -s /bin/bash sysadmin && \
    echo 'sysadmin:Sy54dm1n' | chpasswd && \
    chmod 755 /home/sysadmin

# Tạo user SSH
RUN useradd -m -s /bin/bash system && \
    echo 'system:657sdfh85d' | chpasswd

# Cấu hình SSH
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config && \
    echo 'PermitEmptyPasswords no' >> /etc/ssh/sshd_config && \
    echo 'ChallengeResponseAuthentication no' >> /etc/ssh/sshd_config

# Tạo thư mục SMB
RUN mkdir -p /home/sysadmin/documents && \
    mkdir -p /home/sysadmin/config && \
    mkdir -p /home/sysadmin/backup && \
    chown -R sysadmin:sysadmin /home/sysadmin

# Tạo file hint
RUN echo "SecureCorp Internal File Portal" > /home/sysadmin/documents/readme.txt && \
    echo "" >> /home/sysadmin/documents/readme.txt && \
    echo "SMB Username: sysadmin" >> /home/sysadmin/documents/readme.txt && \
    echo "SMB Password: Sy54dm1n" >> /home/sysadmin/documents/readme.txt && \
    chown sysadmin:sysadmin /home/sysadmin/documents/readme.txt

# Tạo config chứa SSH creds
RUN echo "Username: system" > /home/sysadmin/config/config.txt && \
    echo "Password: 657sdfh85d" >> /home/sysadmin/config/config.txt && \
    echo "Host: smb-target" >> /home/sysadmin/config/config.txt && \
    echo "Port: 22" >> /home/sysadmin/config/config.txt && \
    chown sysadmin:sysadmin /home/sysadmin/config/config.txt

# Copy cấu hình Samba
COPY smb-config/smb.conf /etc/samba/smb.conf

# Copy website
COPY website/ /usr/share/nginx/html/

# Fix nginx root
RUN sed -i 's|root /var/www/html;|root /usr/share/nginx/html;|g' /etc/nginx/sites-enabled/default

# Copy entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 139 445 22 80

CMD ["/entrypoint.sh"]