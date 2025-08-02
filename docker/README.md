# Coffee Journal - Docker Deployment

This directory contains Docker configuration for deploying the Coffee Journal application using Docker Compose.

## Architecture

The application consists of two main services:

- **Backend**: Flask API server with SQLAlchemy ORM
- **Frontend**: React application served by Nginx with API proxying

## Prerequisites

- Docker (20.10 or later)
- Docker Compose (2.0 or later)
- 2GB of available disk space
- Ports 3000 and 5000 available on the host

## Quick Start

1. **Navigate to the docker directory:**
   ```bash
   cd docker
   ```

2. **Build and start the application:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000/api

4. **Stop the application:**
   ```bash
   docker-compose down
   ```

## Database Persistence

The SQLite database is stored in the `../data` directory on your host machine, ensuring data persists between container restarts:

```
coffeejournal/
├── data/
│   └── coffee_journal.db    # Your database file
└── docker/
    ├── docker-compose.yml
    └── ...
```

## Configuration

### File Ownership

To prevent data files from being owned by root when using Docker, update the `.env` file with your actual user and group IDs:

```bash
# Get your user and group IDs
id -u  # Copy this number to UID in .env
id -g  # Copy this number to GID in .env
```

Edit `docker/.env`:
```
UID=1000    # Replace with your user ID  
GID=1000    # Replace with your group ID
```

This ensures files created in `docker/data/` are owned by your user instead of root.

### Environment Variables

#### Backend
- `DATABASE_PATH`: Path to SQLite database file (default: `/app/data/coffee_journal.db`)
- `FLASK_ENV`: Flask environment (default: `production`)
- `PYTHONPATH`: Python module path (default: `/app/src`)

#### Frontend
- `REACT_APP_API_URL`: API base URL (default: `http://localhost:5000/api`)

### Ports

- **Frontend**: 3000 (mapped to container port 80)
- **Backend**: 5000 (mapped to container port 5000)

To change ports, edit the `docker-compose.yml` file:

```yaml
services:
  frontend:
    ports:
      - "8080:80"  # Change 3000 to 8080
  backend:
    ports:
      - "8000:5000"  # Change 5000 to 8000
```

## Database Management

### Initialize with Sample Data

On first run, the database will be empty. To add sample data:

```bash
# Run the initialization script
docker-compose exec backend python /app/docker/init-db.py
```

This adds:
- 3 sample roasters
- 2 bean types (Arabica, Robusta)
- 3 countries (Ethiopia, Colombia, Guatemala)
- 3 brew methods (Pour Over, French Press, Espresso)
- 3 recipes
- 1 sample product with 1 batch

### Backup Database

```bash
# Create a backup
cp ../data/coffee_journal.db ../data/coffee_journal_backup_$(date +%Y%m%d).db
```

### Restore Database

```bash
# Stop the application
docker-compose down

# Restore from backup
cp ../data/coffee_journal_backup_20241215.db ../data/coffee_journal.db

# Start the application
docker-compose up
```

### Access Database Directly

```bash
# Connect to the backend container
docker-compose exec backend bash

# Use sqlite3 to query the database
sqlite3 /app/data/coffee_journal.db
```

## Development vs Production

### Development Mode

For development with hot reloading:

```bash
# Start in development mode
FLASK_ENV=development docker-compose up
```

### Production Mode

For production deployment:

```bash
# Build optimized images
docker-compose build --no-cache

# Start in production mode
docker-compose up -d
```

## Monitoring and Logs

### View Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend

# Follow logs in real-time
docker-compose logs -f
```

### Health Checks

Both services include health checks:

```bash
# Check service status
docker-compose ps

# View health check status
docker inspect coffeejournal-backend | grep Health -A 10
docker inspect coffeejournal-frontend | grep Health -A 10
```

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Check what's using the port
   sudo lsof -i :3000
   sudo lsof -i :5000
   
   # Change ports in docker-compose.yml
   ```

2. **Database permission errors:**
   ```bash
   # Fix data directory permissions
   sudo chown -R $USER:$USER ../data
   chmod 755 ../data
   ```

3. **Build fails:**
   ```bash
   # Clean rebuild
   docker-compose down
   docker system prune -f
   docker-compose build --no-cache
   ```

4. **API connection errors:**
   - Check that both services are running: `docker-compose ps`
   - Verify network connectivity: `docker-compose exec frontend ping backend`
   - Check API URL configuration in frontend

### Performance Tuning

1. **Increase memory limits:**
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 512M
     frontend:
       deploy:
         resources:
           limits:
             memory: 256M
   ```

2. **Enable Nginx compression:**
   The included `nginx.conf` already enables gzip compression for better performance.

## Security Considerations

### Production Deployment

1. **Change default secret key:**
   ```bash
   # Set environment variable
   export FLASK_SECRET_KEY="your-production-secret-key"
   ```

2. **Use HTTPS:**
   - Configure SSL certificates in Nginx
   - Update API URLs to use HTTPS

3. **Database security:**
   - The SQLite database is stored locally and secured by filesystem permissions
   - Consider PostgreSQL for multi-user production environments

4. **Network security:**
   - The application uses a custom Docker network
   - Only necessary ports are exposed

## File Structure

```
docker/
├── README.md                 # This file
├── docker-compose.yml        # Main compose configuration
├── Dockerfile.backend        # Backend (Flask) container
├── Dockerfile.frontend       # Frontend (React) container
├── nginx.conf               # Nginx configuration
└── init-db.py              # Database initialization script
```

## Support

For issues specific to Docker deployment, check:

1. Docker and Docker Compose versions
2. Available disk space and memory
3. Port availability
4. Network connectivity between containers

For application-specific issues, refer to the main project documentation.