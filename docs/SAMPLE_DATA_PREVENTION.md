# Sample Data Prevention in Production

## Overview

Sample data is intended for development and testing purposes only and should never be loaded in production environments. This document explains the safeguards in place and how to manage sample data.

## Safeguards

### 1. Environment Variable Checks

The `generate_sample_data.py` script now checks for two environment variables before loading sample data:

- `PRODUCTION=true` - Prevents sample data loading in production
- `DOCKER_ENV=production` - Additional check for Docker environments

### 2. Production Configuration

The production Docker configuration automatically sets these environment variables:

- In `docker-compose.yml`: `PRODUCTION=true`
- In `Dockerfile`: `DOCKER_ENV=production`

### 3. Development-Only Access

Sample data loading is only accessible through the development script:

```bash
# Development only - with explicit flag
./scripts/dev.sh --load-samples
```

## Cleaning Existing Sample Data

If sample data was accidentally loaded into a production database, use the cleanup script:

```bash
cd backend
poetry run python scripts/clean_sample_data.py
```

This script will:
1. Identify sample data by specific patterns
2. Show what will be removed
3. Request confirmation before deletion
4. Remove sample projects, sessions, and messages

## Sample Data Patterns

Sample data is identified by:
- Projects with paths starting with `/Users/testuser/projects/`
- Sessions with `metadata.version = "1.0.55"`
- Messages associated with sample sessions

## Best Practices

1. **Never run development scripts against production databases**
2. **Always use separate databases for development and production**
3. **Verify environment variables are set correctly in production**
4. **Use the cleanup script if sample data is found in production**

## Verification

To verify no sample data exists in production:

```bash
# Connect to production MongoDB and run:
db.projects.find({ path: /^\/Users\/testuser\/projects\// }).count()
db.sessions.find({ "metadata.version": "1.0.55" }).count()
```

Both queries should return 0 in production environments.
