# Breed Scholar

Mobile-first dog breed learning app with 692 breeds, real images, dark theme, and iOS/PWA support.

## Repo
- GitHub: https://github.com/NicSparks/breed-scholar
- Docker image: `ghcr.io/NicSparks/breed-scholar`

## Quick start
```bash
docker compose up --build
```
Web UI: http://localhost:8000

## Volumes / backup
- `./data` → `/data`
- Database: `/data/dog_breeds.db`
- Static assets: `/data/static/`

## Rebuild database
```bash
docker compose exec web python rebuild_database.py --depth 10
docker compose exec web python download_images.py
```

## Stop
```bash
docker compose down
```

## CI / Docker build
- Docker image is built automatically in GitHub Actions on merge to `main`
- Image is pushed to GitHub Packages: `ghcr.io/NicSparks/breed-scholar`

## License
MIT
