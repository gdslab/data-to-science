FROM node:18-bullseye-slim AS build-stage

WORKDIR /app/

COPY ./package.json ./yarn.lock ./

RUN yarn install

COPY . .

RUN yarn build

FROM nginxinc/nginx-unprivileged:latest

WORKDIR /etc/nginx

COPY --from=build-stage /app/dist /usr/share/nginx/html

COPY docker-entrypoint.sh /
COPY ./frontend.nginx.conf ./conf.d/default.conf

USER root

RUN touch /usr/share/nginx/html/config.json
RUN chown 101:101 /usr/share/nginx/html/config.json
RUN chmod +x /docker-entrypoint.sh

USER 101

ENTRYPOINT ["/docker-entrypoint.sh"]

CMD ["nginx", "-g", "daemon off;"]
