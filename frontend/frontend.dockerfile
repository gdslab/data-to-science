FROM node:18-bullseye-slim

WORKDIR /app/

COPY ./package.json ./yarn.lock ./

RUN yarn install

COPY . .

CMD ["yarn", "run", "dev", "--host", "0.0.0.0", "--port", "8080"]
