# Example: Build Custom Portal using Portal Builder Base Image
# This demonstrates the docker buildx workflow pattern

# Use portal-builder as the build stage
FROM ghcr.io/lumeweb/portal-builder:latest AS builder

# Copy your plugin manifest
COPY portal-plugins.yaml .

# Optional: Copy custom schema
# COPY schema.json /usr/local/share/portal-builder/schema.json

# Build the portal with plugins
# Environment variables can be set here or via ARG
ARG PORTAL_VERSION
ENV PORTAL_VERSION=${PORTAL_VERSION:-develop}

# Run the build script
RUN build-portal

# Final stage: minimal runtime image
FROM alpine:latest

# Install runtime dependencies
RUN apk add --no-cache ca-certificates tzdata libwebp

# Copy the compiled portal binary from builder
COPY --from=builder /dist/portal /usr/local/bin/portal

# Set up non-root user
RUN addgroup -g 1000 portal && \
    adduser -D -u 1000 -G portal portal
USER portal

# Set working directory
WORKDIR /home/portal

# Expose default port
# NOTE: Do NOT declare ports when using Coolify. Uncomment only for other platforms.
# EXPOSE 8080

# Run portal
CMD ["portal"]
