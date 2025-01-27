# syntax=docker/dockerfile:1

FROM nginxproxy/nginx-proxy:1.7

COPY vhost.d/default /etc/nginx/vhost.d/default
COPY custom.conf /etc/nginx/conf.d/custom.conf
