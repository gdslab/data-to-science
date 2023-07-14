FROM node:18-bullseye-slim

WORKDIR /app/

# create unprivileged ps2 user
RUN adduser --system --no-create-home --group ps2

COPY package.json yarn.lock ./
RUN yarn install

COPY . .

USER ps2
