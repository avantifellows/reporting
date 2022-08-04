FROM node:18-alpine

WORKDIR /app

RUN npm install -g dynamodb-admin

CMD ["dynamodb-admin"]