FROM nginxinc/nginx-unprivileged:latest

WORKDIR /etc/nginx

COPY ./common.conf ./common_location.conf ./
COPY ./d2s-proxy.conf ./conf.d/default.conf

EXPOSE 80

ENTRYPOINT ["nginx"]

CMD ["-g", "daemon off;"]
