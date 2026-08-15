# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CI pipeline with security scan, lint, tests, and Docker build
- GitHub Actions workflow for multi-arch Docker image builds
- Branch protection on `main` with PR requirements and status checks
- Rebuild scripts for AKC crawl and database updates
- Image download pipeline for Wikimedia Commons photos
- Placeholder thumbnail generation for breeds without images
- iOS/PWA manifest and mobile meta tags

## [1.0.0] - 2026-08-15

### Added
- Initial release of Breed Scholar
- SQLite database with 692 dog breeds
- Flask web GUI with mobile-first dark theme
- Browse, search, and stats views
- Thumbnail serving for breed images
- Dockerfile and docker-compose.yml with external data mounts
- Rebuild and image download scripts
