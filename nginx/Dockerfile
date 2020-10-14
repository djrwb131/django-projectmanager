FROM nginx:latest-alpine
RUN apk add certbot certbox-nginx
COPY ./nginx.conf /etc/nginx/sites-enabled/api.conf