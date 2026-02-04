# Portal Docker Build Template

A GitHub template repository for building custom LumeWeb Portal Docker images using the [portal-builder](https://github.com/lumeweb/portal-builder) base image.

## What is this template?

This template provides a ready-to-use starting point for building your own custom LumeWeb Portal with custom plugins. It extends the `ghcr.io/lumeweb/portal-builder:latest` base image and includes:

- Example `Dockerfile` with multi-stage build configuration
- Sample `portal-plugins.yaml` with plugin configuration
- GitHub Actions workflow for automated building and pushing
- Complete documentation and examples

## Quick Start

### Coolify Deployment (Recommended)

This template is optimized for Coolify's Dockerfile build pack:

1. Click "Use this template" to create a new repository
2. Clone your new repository
3. Edit `portal-plugins.yaml` to add your desired plugins
4. Push to your Git repository
5. In Coolify:
   - Create a new application
   - Select "Dockerfile" as the build pack
   - Configure your domain
   - Deploy

**Important**: Do not declare ports in Dockerfile when using Coolify. Coolify handles port exposure automatically.

### Option 1: Use this template

1. Click "Use this template" on GitHub to create a new repository
2. Clone your new repository
3. Edit `portal-plugins.yaml` to add your desired plugins
4. Build your custom portal image

### Option 2: Manual setup

```bash
# Clone this repository
git clone https://github.com/lumeweb/portal-docker-build-template.git my-portal
cd my-portal

# Edit portal-plugins.yaml to configure your plugins
vim portal-plugins.yaml

# Build your custom portal
docker build -t my-portal:latest .
```

## Configuration

### Example Files

This template includes example files to help you get started:

- `portal-plugins.yaml` - Main configuration file (edit this for your plugins)
- `portal-plugins.example.yaml` - Example with sample plugins for testing

### portal-plugins.yaml

Edit `portal-plugins.yaml` to configure your portal:

```yaml
# Optional: Portal core version
portalVersion: latest

# List of plugins to include
plugins:
  - module: go.lumeweb.com/portal-plugin-dashboard
    version: latest
  - module: go.lumeweb.com/portal-plugin-auth
    version: v2.0.0
```

### Build Arguments

You can also configure the build using Docker build arguments:

```bash
# Build with specific portal version
docker build --build-arg PORTAL_VERSION=develop -t my-portal:latest .

# Build with plugins from environment variable
docker build --build-arg PLUGINS="go.lumeweb.com/portal-plugin-dashboard@latest" -t my-portal:latest .
```

## Available Plugins

See the [LumeWeb Portal documentation](https://docs.lumeweb.com) for a list of available plugins.

## Building Locally

### Basic build

```bash
docker build -t my-portal:latest .
```

### Build with specific portal version

```bash
docker build --build-arg PORTAL_VERSION=develop -t my-portal:latest .
```

### Multi-platform build

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t my-portal:latest \
  --load \
  .
```

## Running Your Portal

### For Coolify Deployment

When deploying to Coolify, simply push your code and configure the application in the Coolify dashboard. Coolify will handle:
- Port exposure automatically
- Network configuration
- Proxy routing (if using Traefik)

### For Local Docker Testing

When testing locally with Docker (not Coolify):

```bash
# Run the portal
docker run -p 8080:8080 my-portal:latest

# Run with custom configuration
docker run -p 8080:8080 \
  -v $(pwd)/config:/home/portal/config \
  my-portal:latest
```

## Testing

See [TESTING.md](TESTING.md) for comprehensive testing instructions including:
- Quick test guide
- Manual testing with build arguments
- Validation testing
- Multi-platform builds
- Debugging tips
- Common issues and solutions

## GitHub Actions

This template includes a GitHub Actions workflow that automatically:

1. Builds your custom portal image on push to `main`/`develop` branches or tags
2. Pushes the image to GitHub Container Registry (GHCR)
3. Supports multi-platform builds (linux/amd64, linux/arm64)

**Coolify Note**: When using GitHub Actions with Coolify, you can either:
- Let Coolify build from your Git repository directly (recommended)
- Use the GHCR image built by GitHub Actions and deploy it in Coolify using the "Docker Image" build pack

If deploying the GHCR image to Coolify, use the "Docker Image" build pack instead of "Dockerfile".

### Setup

1. Enable GitHub Actions in your repository settings
2. Ensure your repository has the necessary permissions for packages
3. Push to the `main` or `develop` branch or create a tag to trigger a build

### Manual trigger

You can manually trigger a build from the Actions tab in GitHub and specify a portal version.

## Customization

### Dockerfile

The `Dockerfile` is structured as a multi-stage build:

1. **Builder stage**: Uses `portal-builder` to compile your custom portal
2. **Runtime stage**: Uses a minimal Alpine image to run the portal

You can customize:

- Runtime dependencies in the Alpine stage (includes libwebp for WebP support)
- Port exposure (EXPOSE is commented out per Coolify recommendations)
- User configuration
- Working directory
- Environment variables

### Workflow

The `.github/workflows/build-docker.yml` workflow can be customized:

- Add more build platforms
- Change registry destination
- Add additional build steps
- Configure caching strategies

## Examples

### Quick test with example plugins

```bash
# Test with the example configuration
docker build -f Dockerfile -t my-portal-test .
```

### Minimal portal with no plugins

```yaml
# portal-plugins.yaml
portalVersion: latest
plugins: []
```

### Portal with specific plugin versions

```yaml
plugins:
  - module: go.lumeweb.com/portal-plugin-dashboard
    version: v2.1.0
  - module: go.lumeweb.com/portal-plugin-auth
    version: v2.0.5
```

### Portal from environment variables

```dockerfile
# In Dockerfile
FROM ghcr.io/lumeweb/portal-builder:latest AS builder
ARG PLUGINS
ENV PLUGINS=${PLUGINS}
RUN build-portal

FROM alpine:latest
COPY --from=builder /dist/portal /usr/local/bin/portal
CMD ["portal"]
```

Build:
```bash
docker build --build-arg PLUGINS="go.lumeweb.com/portal-plugin-dashboard@latest" -t my-portal .
```

## Troubleshooting

### Coolify-Specific Issues

**"Port is already allocated" error:**
- Ensure `EXPOSE` is commented out in your Dockerfile
- Coolify manages port binding automatically

**Application not accessible after deployment:**
- Verify your domain is correctly configured in Coolify
- Check that the application is running in the Coolify dashboard
- Review application logs in Coolify

**Build fails in Coolify:**
- Check the build logs in Coolify for specific error messages
- Verify your portal-plugins.yaml follows the correct format
- Ensure all plugin versions are valid

### Build fails with plugin not found

Ensure the plugin module path is correct and the version exists. Check the plugin's repository for available versions.

### Build fails with schema validation error

The `portal-plugins.yaml` must conform to the JSON schema. Check that:
- `module` is a valid Go module path
- `version` is a valid semantic version or `latest`

### Slow builds

The portal-builder image includes a pre-populated Go module cache, but custom plugins may still need to be downloaded. Consider using Docker layer caching:

```bash
docker build --cache-from my-portal:latest -t my-portal:latest .
```

## Support

- [LumeWeb Portal Documentation](https://docs.lumeweb.com)
- [portal-builder Repository](https://github.com/lumeweb/portal-builder)
- [GitHub Issues](https://github.com/lumeweb/portal-docker-build-template/issues)

## License

This template is licensed under the same license as the LumeWeb Portal project.
