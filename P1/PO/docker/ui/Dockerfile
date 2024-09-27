# Use Nginx to serve static files
FROM nginx:alpine

# Set the working directory inside the container
WORKDIR /usr/share/nginx/html

# Remove the default Nginx files
RUN rm -rf ./*

# Copy all your static files (HTML, CSS, JS) into the Nginx web root
COPY ./app .

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
