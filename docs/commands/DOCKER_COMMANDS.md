# Docker Commands Used In This Project

Last updated: 2026-03-30
Scope: Container build, run, and publishing operations reflected in repository workflows and Docker configuration.

## How To Read This File

Each command includes:
- What it is used for
- When to use it
- Where to run it
- How it works
- Recommended tags/options (flags) and why
- Alternatives

---

## 1) Build Image Locally

Command:

```bash
docker build -t educational-equity-flow:local .
```

Used for:
- Build local image from Dockerfile for testing.

When to use:
- Before deployment or docker-compose runs

Where to use:
- Repository root (where Dockerfile exists)

How it works:
- Sends build context to Docker daemon and executes Dockerfile stages.

Tags/options and why:
- -t sets image tag for human-readable reference
- Use :local for non-release local testing

Alternatives:
- docker compose build dashboard

---

## 2) Run Dashboard Container

Command:

```bash
docker run --rm -p 8501:8501 educational-equity-flow:local
```

Used for:
- Launch dashboard from built image.

When to use:
- Manual container validation

Where to use:
- Any host with Docker

How it works:
- Runs image and maps host port to container Streamlit port.

Tags/options and why:
- --rm cleans up container after stop
- -p 8501:8501 exposes UI to host browser

Alternatives:
- docker compose up dashboard

---

## 3) Compose Up (Full Local Stack)

Command:

```bash
docker compose up --build
```

Used for:
- Start dashboard service (and optional artifacts service) using compose file.

When to use:
- Non-technical demos or reproducible local container stack

Where to use:
- Repository root (docker-compose.yml present)

How it works:
- Builds image if needed and starts declared services with network/volumes.

Tags/options and why:
- --build ensures latest Dockerfile changes are used
- -d can be added for detached mode

Alternatives:
- docker compose up dashboard

---

## 4) Compose Down

Command:

```bash
docker compose down
```

Used for:
- Stop and remove compose-managed containers/network.

When to use:
- End of demo/test session

Where to use:
- Repository root

How it works:
- Gracefully stops services and cleans compose resources.

Tags/options and why:
- --volumes if you also want to remove named volumes

Alternatives:
- docker stop <container>

---

## 5) Inspect Running Containers

Command:

```bash
docker ps
```

Used for:
- Confirm services are running and ports are mapped.

When to use:
- Troubleshooting availability issues

Where to use:
- Any Docker host

How it works:
- Lists active containers and metadata.

Tags/options and why:
- -a includes stopped containers for failure diagnosis

Alternatives:
- docker compose ps for compose-scoped view

---

## 6) View Container Logs

Command:

```bash
docker logs educational-equity-flow-dashboard
```

Used for:
- Inspect startup/runtime output for dashboard service.

When to use:
- Debugging launch failures or runtime errors

Where to use:
- Any Docker host running the container

How it works:
- Prints stdout/stderr history from container runtime.

Tags/options and why:
- -f for follow mode
- --tail 200 for recent output only

Alternatives:
- docker compose logs dashboard

---

## 7) Publish Tags (CI Pattern)

CI uses action-driven equivalent of:

```bash
docker buildx build --push -t ghcr.io/<owner>/<repo>:<tag> .
```

Used for:
- Build and push images to registries in GitHub Actions.

When to use:
- On master changes affecting Docker/app sources
- Scheduled weekly rebuilds for security updates

Where to use:
- CI runner environment

How it works:
- Buildx supports cache and multi-platform-oriented workflows.

Tags/options and why:
- Recommended tag set in CI:
  - branch tag: tracks branch head image
  - sha tag: immutable traceability to commit
  - semver tags: release lineage
  - latest: convenience for default branch consumers

Alternatives:
- Manual docker push from local environment (less reproducible)

---

## 8) Registry Login (CI Equivalent)

Common patterns:

```bash
docker login ghcr.io
docker login
```

Used for:
- Authenticate before pushing images.

When to use:
- Manual publish workflows or custom CI

Where to use:
- CI runner or local workstation

How it works:
- Stores auth token/credentials for registry operations.

Tags/options and why:
- Prefer token-based auth over passwords

Alternatives:
- GitHub Actions docker/login-action (used by this project)

---

## Docker Tag Strategy For This Project

Recommended tags and why:
- latest: simple default pull for non-technical consumers
- <git-sha>: exact reproducibility and rollback
- <semver>: stable release channels (for milestone demos/releases)
- <branch>: integration/testing channel

Avoid:
- Only latest without sha/semver fallback (hard to trace)
