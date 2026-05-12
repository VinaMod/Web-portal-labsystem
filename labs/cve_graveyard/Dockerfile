FROM tomcat:7.0.70-jre8

# Enable PUT by setting readonly=false in the default servlet
RUN sed -i '/<servlet-name>default<\/servlet-name>/,/<\/servlet>/ s/<load-on-startup>1<\/load-on-startup>/<init-param>\n            <param-name>readonly<\/param-name>\n            <param-value>false<\/param-value>\n        <\/init-param>\n        <load-on-startup>1<\/load-on-startup>/' conf/web.xml

# Create an entrypoint script
# This script generates the dynamic flag based on the EMAIL environment variable
# and the current date (Asia/Ho_Chi_Minh timezone) upon container startup.
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Remove default tomcat page and copy premium UI
RUN rm -rf /usr/local/tomcat/webapps/ROOT/*
COPY src/index.html /usr/local/tomcat/webapps/ROOT/index.html

ENTRYPOINT ["/entrypoint.sh"]
