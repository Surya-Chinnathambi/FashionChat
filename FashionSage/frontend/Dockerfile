# Stage 1: Build
FROM node:18-alpine AS build

WORKDIR /app

# Copy package.json and lock first
COPY package*.json ./

# Install deps
RUN npm install

# Copy the rest of the source
COPY . .

# Build for production
RUN npm run build

# Stage 2: Nginx serve
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
