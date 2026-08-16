# Breed Scholar

> Mobile-first dog breed learning app with 692 breeds, real images, dark theme, iOS/PWA support, and automated monthly AKC updates.

## What it is

Breed Scholar is a web app for learning dog breeds by sight and registry. It includes a browseable catalog, search/filter, image thumbnails, stats, and a setup path for flashcards/quizzes. The app is designed to feel like a native iOS experience via PWA/home-screen install.

## Highlights

- 692 breeds indexed: AKC, FCI, and Non-Recognized
- Mobile-first dark theme
- iOS/PWA-ready with standalone mode
- Thumbnails + full-size cached images
- SQLite-backed Flask API
- GitHub Actions CI with security scan, lint, tests
- Automatic Docker image build/push on merge to `main`
- Scheduled AKC crawl every 30 days with deduplication

## Repo

- GitHub: https://github.com/NicSparks/breed-scholar
- Docker image: `ghcr.io/NicSparks/breed-scholar`

## Quick start

```bash
git clone https://github.com/NicSparks/breed-scholar.git
cd breed-scholar
docker compose up --build
```

Open: http://localhost:8000

### Add to iPhone home screen

1. Open Safari
2. Go to http://localhost:8000 or your server URL
3. Tap Share → Add to Home Screen
4. Launch as standalone app

## Volumes / backup

- `./data` → `/data`
- Database: `/data/dog_breeds.db`
- Static assets: `/data/static/`

Backup by copying the `data` directory.

## Rebuild database

```bash
docker compose exec web python rebuild_database.py --depth 10
docker compose exec web python download_images.py
```

## Scheduled AKC crawl

A GitHub Actions workflow runs automatically every 30 days to crawl AKC, update the database, and push changes. It deduplicates breeds by normalized name before indexing.

Workflow: `.github/workflows/scheduled-crawl.yml`

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

## CI / Docker build

- Security scan: CodeQL + Bandit + pip-audit
- Lint: Ruff + HTML validation
- Tests: DB integrity + JSON validation
- Docker build/push: multi-arch `linux/amd64`, `linux/arm64`

Image pushed to GitHub Packages on successful merge to `main`.

## API

### GET /api/breeds
List breeds with pagination, search, registry/group filters.

Query params:
- `search` - name search
- `registry` - `akc`, `fci`, `non`
- `group` - group name filter
- `page` - page number
- `per_page` - results per page

### GET /api/breeds/all
Return all breeds.

### GET /api/stats
Return totals and top ranked breeds.

### GET /static/thumbs/<id>.jpg
Serve breed thumbnail.

### GET /manifest.json
PWA manifest.

## License

MIT
