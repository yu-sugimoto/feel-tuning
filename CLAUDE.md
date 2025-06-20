# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Music-swipe is a Japanese music recommendation app that analyzes photos to recommend songs through a swipe interface. The system uses OpenAI GPT-4o for image mood analysis and implements a 3-phase recommendation algorithm.

## Architecture

**Backend**: FastAPI with SQLAlchemy ORM, PostgreSQL database, JWT authentication
**Frontend**: React Native/Expo with TypeScript and file-based routing
**Deployment**: Docker containerized with multi-container setup

## Common Development Commands

### Backend Development
```bash
# Start full environment (recommended)
docker-compose up --build

# Manual development setup
cd backend
pip install -r requirements.txt
alembic upgrade head
python app/init_data.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Development
```bash
cd frontend/music-swipe
npm install
npx expo start
# Choose platform: Android emulator, iOS simulator, or Expo Go app
```

### Database Operations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Reset database (development)
docker-compose down -v && docker-compose up --build
```

## Key Architecture Components

### Backend Structure
- **Models**: User, SwipeHistory, PlaylistHistory with proper relationships
- **Services**: JWT authentication, password hashing, OpenAI image analysis
- **Recommendation Engine**: 3-phase algorithm using mood similarity matrices and instrument correlation
- **API Endpoints**: /signup, /login, /photo (mood analysis), /swipe (recommendation)

### Frontend Structure
- **File-based routing** with expo-router
- **Key screens**: index (landing), login, signup, photo (upload), swipe (music interface)
- **State**: Local state with AsyncStorage for JWT token persistence
- **UI**: Consistent blue theme (#2C7FD5) with background images

### Database Schema
- **users**: Authentication and profile data
- **swipe_history**: User interaction tracking (song_id, liked boolean)
- **playlist_history**: Generated playlists with image paths and song JSON

## Current Implementation Status

**Completed**: Backend API, user authentication, photo upload, mood analysis
**In Progress**: Swipe interface (swipe.tsx is empty and needs implementation)
**TODO**: History screen, analysis screen, complete photo-to-swipe flow integration

## Environment Variables

**Backend**: DATABASE_URL, SECRET_KEY, ALGORITHM, API_KEY (OpenAI)
**Frontend**: API_URL (backend server address)

## Data Files

The backend uses pre-processed data files in `backend/data/`:
- `filtered_songs_4_or_more_tags.json`: Main song database with embeddings
- `mood_similarity.json`: Mood correlation matrix
- `mood_instrument_similarity.json`: Mood-instrument correlation data

## Testing and Linting

Currently no automated testing or linting setup. When implementing, check package.json for available scripts first.