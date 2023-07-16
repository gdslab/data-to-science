FROM nginxinc/nginx-unprivileged:latest

WORKDIR /etc/nginx

COPY ./common.conf ./common_location.conf ./
COPY ./ps2.dev.conf ./conf.d/default.conf

EXPOSE 80

ENTRYPOINT ["nginx"]

CMD ["-g", "daemon off;"]
