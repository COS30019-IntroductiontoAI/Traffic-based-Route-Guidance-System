# Use a lightweight Node.js image
FROM node:20-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy only frontend source needed by Vite.
# Keeping the copy scope small improves layer cache reuse and rebuild speed.
COPY frontend ./frontend

# Expose the port your React dev server runs on (5173 for Vite)
EXPOSE 5173

# Command to start the frontend dev server
CMD ["npm", "run", "dev", "--", "--host"]

