# Use the specified version of Node.js
FROM node:21.3.0-alpine AS builder

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Run the build command
RUN npm run build

# Use a minimal Node.js image for serving the build
FROM node:21.3.0-alpine

WORKDIR /app

# Copy the build output from the builder stage
COPY --from=builder /app/dist /app

# Install a simple HTTP server
RUN npm install -g serve

# Expose the port the app runs on
EXPOSE 3000

# Start the HTTP server
CMD ["serve", "-s", ".", "-l", "3000"]
