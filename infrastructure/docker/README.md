## `infrastructure/docker/`

Docker assets for running the repository in a container.

The development image uses Python 3.14 and checksum-verified uv 0.13.0.
The root `.python-version` is copied before dependency installation so the
container uses the repository's declared runtime. Verify an actual container
build and runtime before claiming operational acceptance.

### Start

See `docs/CLOUD_DEPLOY.md` for the recommended usage patterns.
