FROM nginxinc/nginx-unprivileged:1.29

ARG DEFAULT_CONF

WORKDIR /etc/nginx

EXPOSE 80

# will copy conf templates from templates dir to /etc/nginx/conf.d/ substituting any
# environment variables present in the templates
COPY docker-entrypoint.sh /
COPY 20-envsubst-on-templates.sh /docker-entrypoint.d
COPY templates/${DEFAULT_CONF}/default.conf.template /etc/nginx/templates/

ENTRYPOINT ["/docker-entrypoint.sh"]

CMD ["nginx", "-g", "daemon off;"]