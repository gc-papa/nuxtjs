# Stage 1: Build the Nuxt 3 application
FROM node:20-alpine AS build

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application files
COPY . .

# Build the application
RUN npm run build

# Stage 2: Serve the Nuxt 3 application
FROM node:20-alpine

# Set the working directory in the container
WORKDIR /app

# Copy only necessary files from the build stage
COPY --from=build /app/.output /app/.output
COPY --from=build /app/package*.json ./

# Install production dependencies only
RUN npm install --production

# Expose the required port for Cloud Run
# Cloud Run requires listening on $PORT
EXPOSE 3000

# Command to run the application
CMD ["node", ".output/server/index.mjs"]
