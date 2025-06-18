# --- Stage 1: Build ---
# Use a slim Go image for the build environment
FROM golang:1.22-alpine AS builder

# Set the Current Working Directory inside the container
WORKDIR /app

# Copy the Go module files from the submodule directory
COPY ./aistudio-build-proxy/go.mod ./aistudio-build-proxy/go.sum ./

# Set the Go proxy to a reliable one in China
ENV GOPROXY=https://goproxy.cn,direct
RUN go mod download

# Copy the source code from the submodule directory
COPY ./aistudio-build-proxy/ .

# Build the Go app
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /proxy-server .

# --- Stage 2: Final ---
# Use a minimal base image for the final container
FROM alpine:latest

# Add ca-certificates to make HTTPS calls and netcat for health checks
RUN apk --no-cache add ca-certificates netcat-openbsd

# Set the Current Working Directory inside the container
WORKDIR /root/

# Copy the pre-built binary file from the previous stage
COPY --from=builder /proxy-server .

# Expose port 5345
EXPOSE 5345

# Command to run the executable
CMD ["./proxy-server"]