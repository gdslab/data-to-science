FROM nginxinc/nginx-unprivileged:latest

ARG DEFAULT_CONF

WORKDIR /etc/nginx

COPY ./${DEFAULT_CONF} ./conf.d/default.conf

EXPOSE 80

ENTRYPOINT ["nginx"]

CMD ["-g", "daemon off;"]