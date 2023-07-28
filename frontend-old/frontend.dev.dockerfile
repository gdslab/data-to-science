FROM node:18-bullseye-slim as build-stage

WORKDIR /app/

COPY ./package.json ./yarn.lock ./

RUN yarn install

COPY . .
