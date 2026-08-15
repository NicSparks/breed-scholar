# Breed Scholar

Dockerized dog breed web app backed by SQLite, with rebuild and backup workflows.

## Run
```bash
docker compose up --build
```
Web UI: http://localhost:8000

## Volumes / backup
- `./data` → `/data`
- Database: `/data/dog_breeds.db`
- Static assets: `/data/static/`
- Uploads: `/data/uploads/`

## Rebuild database
```bash
docker compose exec web python rebuild_database.py --depth 10
```

## Stop
```bash
docker compose down
```
