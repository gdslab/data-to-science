FROM node:18-bullseye-slim as build-stage

WORKDIR /app/

COPY ./frontend/package.json ./frontend/yarn.lock ./

RUN yarn install

COPY ./frontend .

RUN yarn build

FROM nginxinc/nginx-unprivileged:latest

WORKDIR /etc/nginx

COPY --from=build-stage /app/dist /usr/share/nginx/html

COPY ./nginx/common.conf ../nginx/common_location.conf ./

ENTRYPOINT ["nginx"]

CMD ["-g", "daemon off;"]
