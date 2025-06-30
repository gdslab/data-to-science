FROM node:18-bullseye-slim

WORKDIR /app/

COPY ./package.json ./yarn.lock ./

RUN yarn install

COPY . .

# Create the config file in the public directory where yarn dev server can serve it
RUN touch /app/public/config.json

COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]

CMD ["yarn", "run", "dev", "--host", "0.0.0.0", "--port", "8080"]
