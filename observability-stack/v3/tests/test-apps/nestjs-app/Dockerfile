FROM node:18-slim
WORKDIR /app
COPY package.json .
RUN npm install
COPY main.ts .
RUN npm install -g typescript @nestjs/cli
RUN tsc main.ts --outDir dist --experimentalDecorators --emitDecoratorMetadata
ENV NODE_ENV=production
EXPOSE 3000
CMD ["npm", "start"]