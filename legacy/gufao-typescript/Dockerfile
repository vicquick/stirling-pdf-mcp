# Use Node.js LTS image
FROM node:20-slim

# Set working directory
WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./
COPY tsconfig.json ./

# Install all dependencies (including dev dependencies for build)
RUN npm ci

# Copy TypeScript source
COPY src/ ./src/

# Build TypeScript
RUN npm run build

# Remove dev dependencies after build
RUN npm prune --production

# Set Node environment to production
ENV NODE_ENV=production

# Create non-root user (use node user that already exists)
RUN chown -R node:node /app

# Switch to non-root user
USER node

# Run the server
CMD ["node", "dist/index.js"]
