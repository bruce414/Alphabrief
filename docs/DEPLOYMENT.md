# Alphabrief v0.3 Deployment

## Version

`v0.3 MVP`

## Purpose

This document describes the recommended deployment shape for Alphabrief v0.3.

## Recommended Deployment Shape

For MVP, use simple and reliable infrastructure.

```text
Frontend: Vercel, Netlify, or AWS Amplify
Backend: Render, Fly.io, Railway, AWS Elastic Beanstalk, or AWS ECS later
Database: Managed PostgreSQL
```

## Environment Separation

Recommended environments:

```text
local
staging
production
```

## Frontend Deployment

Frontend should be deployed as a static React/Vite app.

Required environment variable:

```text
VITE_API_BASE_URL=https://api.alphabrief.example.com/api/v1
```

## Backend Deployment

Backend should be deployed as a Spring Boot service.

Required environment variables:

```text
SPRING_PROFILES_ACTIVE=prod
DATABASE_URL=replace_me
DATABASE_USERNAME=replace_me
DATABASE_PASSWORD=replace_me
AI_PROVIDER_API_KEY=replace_me
MARKET_DATA_API_KEY=replace_me
NEWS_API_KEY=replace_me
FRONTEND_BASE_URL=https://alphabrief.example.com
BACKEND_BASE_URL=https://api.alphabrief.example.com
```

## Database Deployment

Use managed PostgreSQL.

Recommended requirements:

- Automated backups
- SSL enabled
- Private networking if available
- Separate production credentials
- Migration support through Flyway

## Deployment Checklist

Before deploying:

- Environment variables are configured
- Database is reachable from backend
- Flyway migrations run successfully
- Frontend API URL points to production backend
- CORS allows production frontend
- API keys are not exposed to frontend
- Logging is enabled
- Error tracking is configured if available
- HTTPS is enabled

## MVP Deployment Principle

Choose boring infrastructure first.

The goal is to ship Alphabrief, not build a tiny cloud kingdom with seven drawbridges.
