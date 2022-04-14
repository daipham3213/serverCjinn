#Nginx image
FROM nginx:alpine

#Delete the original configuration file, create static resource folder and SSL certificate save folder
RUN rm /etc/nginx/conf.d/default.conf \
&& mkdir -p /usr/share/nginx/html/static \
&& mkdir -p /usr/share/nginx/html/media \
&& mkdir -p /usr/share/nginx/ssl

#Add profile
ADD ./nginx.conf /etc/nginx/conf.d/