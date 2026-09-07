FROM node:22-alpine
WORKDIR /app
COPY server/package.json server/package.json
COPY server/src server/src
COPY server/scripts server/scripts
COPY site site
COPY brand brand
COPY data data
WORKDIR /app/server
ENV NODE_ENV=production PORT=8787 UG_DB=/data/ug.sqlite
VOLUME ["/data"]
EXPOSE 8787
CMD ["node", "src/index.js"]
