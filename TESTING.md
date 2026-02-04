# Testing Portal Build Template

This guide demonstrates how to test your custom portal build using this template.

## Quick Test

### 1. Build Your Custom Portal

```bash
docker build -t my-portal .
```

### 2. Run the Built Portal

**For local Docker testing:**
```bash
docker run -p 8080:8080 my-portal
```

**For Coolify deployment:**
Do not specify port mappings. Coolify handles port exposure automatically.

### 3. Test the Portal

**Local testing:**
Open your browser and navigate to `http://localhost:8080` to verify the portal is running.

**Coolify deployment:**
Access your portal through the domain configured in Coolify.

## Manual Testing

### Test with Build Arguments

```bash
# Build with specific portal version
docker build --build-arg PORTAL_VERSION=develop -t my-portal-dev .

# Build with multiple build arguments
docker build \
  --build-arg PORTAL_VERSION=develop \
  --build-arg PLUGINS="go.lumeweb.com/portal-plugin-core@develop" \
  -t my-portal-custom .
```

### Test with Environment Variables

Modify your Dockerfile to use environment variables:

```dockerfile
FROM ghcr.io/lumeweb/portal-builder:latest AS builder
ARG PLUGINS
ENV PLUGINS=${PLUGINS}
RUN build-portal
```

Then build:
```bash
docker build --build-arg PLUGINS="go.lumeweb.com/portal-plugin-dashboard@latest" -t my-portal .
```

## Validation Testing

### Validate Manifest Locally

Before building, validate your `portal-plugins.yaml`:

```bash
# Install check-jsonschema
pip install check-jsonschema

# Validate against the schema from portal-builder
# (You'll need to download schema.json from portal-builder first)
check-jsonschema --schemafile schema.json portal-plugins.yaml
```

## Buildx Multi-Platform

Test building for multiple platforms:

```bash
# Create a new builder instance if needed
docker buildx create --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t my-portal:latest \
  --load \
  .
```

## Debugging

### View Build Logs

```bash
# Build with verbose output
docker build --progress=plain -t my-portal .
```

### Inspect the Built Image

```bash
# View image details
docker inspect my-portal

# Check the portal binary
docker run --rm my-portal ls -la /usr/local/bin/portal

# Check portal version
docker run --rm my-portal portal --version
```

### Run Container with Shell Access

```bash
# Run container with shell for debugging
docker run -it --rm --entrypoint sh my-portal

# Once inside, run portal manually
portal --help
```

## Common Issues

### Build fails with plugin not found

- Verify the plugin module path is correct
- Check that the version exists in the plugin's repository
- Try using `latest` or `develop` if a specific version fails

### Build fails with schema validation error

- Ensure your `portal-plugins.yaml` follows the correct format
- Check that `module` is a valid Go module path
- Verify that `version` is a valid semantic version or `latest`

### Slow builds

- Use Docker layer caching: `docker build --cache-from my-portal:latest -t my-portal .`
- Consider using a local registry for caching
- The portal-builder image includes a pre-populated Go module cache for faster builds

### Portal won't start

- Check if the port is already in use: `lsof -i :8080`
- Review container logs: `docker logs my-portal`
- Verify the portal binary was copied correctly

## Performance Testing

### Test Build Performance

```bash
time docker build -t my-portal .
```

### Test Runtime Performance

```bash
# Run with resource limits
docker run -p 8080:8080 \
  --memory="512m" \
  --cpus="1.0" \
  my-portal

# Monitor resource usage
docker stats
```

## Integration Testing

### Test with Custom Configuration

```bash
# Create a test configuration directory
mkdir -p ./config
echo '{"port": 8080}' > ./config/portal.json

# Run with mounted configuration
docker run -p 8080:8080 \
  -v $(pwd)/config:/home/portal/config \
  my-portal
```

### Test with Multiple Plugins

Update `portal-plugins.yaml` with multiple plugins:

```yaml
plugins:
  - module: go.lumeweb.com/portal-plugin-core
    version: develop
  - module: go.lumeweb.com/portal-plugin-dashboard
    version: develop
  - module: go.lumeweb.com/portal-plugin-ipfs
    version: develop
```

Build and test:
```bash
docker build -t my-portal-multi .
docker run -p 8080:8080 my-portal-multi
```
## Coolify Deployment

### Pre-Deployment Checklist

Before deploying to Coolify:

1. **Verify Dockerfile**: Ensure `EXPOSE` is commented out (it should be by default)
2. **Test locally**: Run local tests to ensure your portal builds correctly
3. **Check portal-plugins.yaml**: Verify your plugin configuration

### Deployment Steps

1. Push your code to a Git repository that Coolify can access
2. In Coolify, create a new application
3. Select "Dockerfile" as the build pack
4. Configure your environment variables if needed
5. Set up your domain in Coolify
6. Deploy

### Coolify-Specific Notes

- **Port Management**: Coolify automatically manages port exposure. Do not override this.
- **Environment Variables**: Set `PORTAL_VERSION`, `PLUGINS`, etc. in Coolify's environment variables section.
- **Build Arguments**: Configure build arguments in Coolify's application settings if needed.

### Common Coolify Issues

**"Port is already allocated" error:**
- Ensure `EXPOSE` is commented out in your Dockerfile
- Do not specify port mappings in Coolify's deployment settings

**Application not accessible:**
- Verify your domain is correctly configured in Coolify
- Check that the application is running in Coolify dashboard
- Review application logs in Coolify

## Cleanup

### Remove Test Images

```bash
# Remove specific image
docker rmi my-portal

# Remove all test images
docker images | grep my-portal | awk '{print $3}' | xargs docker rmi

# Clean up unused resources
docker system prune
```

### Remove Test Containers

```bash
# Stop all running containers
docker stop $(docker ps -q)

# Remove all containers
docker rm $(docker ps -aq)
```
