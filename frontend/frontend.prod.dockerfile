FROM node:18-bullseye-slim AS build-stage

WORKDIR /app/

COPY ./package.json ./yarn.lock ./

RUN yarn install

COPY . .

RUN yarn build

FROM nginxinc/nginx-unprivileged:latest

WORKDIR /etc/nginx

COPY --from=build-stage /app/dist /usr/share/nginx/html

COPY ./frontend.nginx.conf ./conf.d/default.conf

ENTRYPOINT ["nginx"]

CMD ["-g", "daemon off;"]
