FROM nginx:1.27-alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/nginx.conf
COPY sites/ /etc/nginx/conf.d/

EXPOSE 80 443
