# Coffee Journal - Docker Setup Guide

This guide will help you deploy the Coffee Journal application using Docker on any system.

## 🎯 Quick Start (TL;DR)

```bash
# 1. Navigate to the docker directory
cd docker

# 2. Start the application
./start.sh --build --init-db

# 3. Open your browser
# Frontend: http://localhost:3000
# API: http://localhost:5000/api
```

## 📋 Prerequisites

Before you begin, ensure you have:

- **Docker** (version 20.10 or later)
- **Docker Compose** (version 2.0 or later)
- **2GB** of available disk space
- **Ports 3000 and 5000** available on your system

### Installing Docker

#### Ubuntu/Debian:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### macOS:
Download and install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)

#### Windows:
Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)

## 🚀 Deployment Options

### Option 1: Quick Start Script (Recommended)

```bash
cd docker

# Start with sample data
./start.sh --build --init-db

# Start in background
./start.sh --detached --init-db

# View all options
./start.sh --help
```

### Option 2: Manual Docker Compose

```bash
cd docker

# Build and start
docker-compose up --build

# Add sample data (in another terminal)
docker-compose exec backend python /app/docker/init-db.py

# Start in background
docker-compose up -d
```

## 🗄️ Database Management

### Database Location

Your SQLite database is stored on your local filesystem:
```
coffeejournal/
├── data/
│   └── coffee_journal.db    # Your persistent database
└── docker/
    └── ...
```

This ensures your data survives container restarts and updates.

### Initialize with Sample Data

```bash
# Add sample coffee data to get started
docker-compose exec backend python /app/docker/init-db.py
```

This creates:
- 3 sample roasters (Blue Bottle, Stumptown, Intelligentsia)
- Bean types, countries, brew methods
- 1 sample coffee product with a batch

### Backup Your Data

```bash
# Create a timestamped backup
cp data/coffee_journal.db data/backup_$(date +%Y%m%d_%H%M%S).db

# Or use the script
cd docker
docker-compose exec backend sqlite3 /app/data/coffee_journal.db ".backup /app/data/backup.db"
```

### Restore from Backup

```bash
# Stop the application
cd docker
./stop.sh

# Replace the database
cp data/your_backup.db data/coffee_journal.db

# Restart
./start.sh
```

## 🔧 Configuration

### Change Ports

Edit `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "8080:80"    # Change 3000 to 8080
  backend:
    ports:
      - "8000:5000"  # Change 5000 to 8000
```

### Environment Variables

Create a `.env` file in the docker directory:

```bash
# .env file
REACT_APP_API_URL=http://localhost:5000/api
DATABASE_PATH=/app/data/coffee_journal.db
FLASK_ENV=production
```

## 📊 Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Check Status

```bash
# Service status
docker-compose ps

# Resource usage
docker stats
```

### Health Checks

```bash
# Backend health
curl http://localhost:5000/api/roasters

# Frontend health
curl http://localhost:3000
```

## 🛠️ Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find what's using the port
sudo lsof -i :3000
sudo lsof -i :5000

# Change ports in docker-compose.yml or stop conflicting services
```

#### Build Failures
```bash
# Clean rebuild
docker-compose down
docker system prune -f
docker-compose build --no-cache
```

#### Permission Errors
```bash
# Fix data directory permissions
sudo chown -R $USER:$USER data/
chmod 755 data/
```

#### API Connection Issues
```bash
# Check if services are running
docker-compose ps

# Test network connectivity
docker-compose exec frontend ping backend

# Check logs for errors
docker-compose logs backend
```

### Reset Everything

```bash
# ⚠️ WARNING: This deletes all data!
./stop.sh --clean
rm -rf ../data
./start.sh --build --init-db
```

## 🔒 Security Considerations

### For Production Use

1. **Change the secret key:**
   ```yaml
   environment:
     - FLASK_SECRET_KEY=your-super-secret-production-key
   ```

2. **Use HTTPS:**
   - Configure SSL certificates in nginx.conf
   - Update REACT_APP_API_URL to use https://

3. **Secure the database:**
   - The SQLite file is secured by filesystem permissions
   - Consider PostgreSQL for multi-user environments

4. **Network security:**
   - Use a reverse proxy (nginx/apache) in production
   - Implement proper firewall rules

## 📁 File Structure

```
docker/
├── README.md              # Main documentation
├── DOCKER_SETUP.md        # This setup guide
├── docker-compose.yml     # Main Docker Compose config
├── Dockerfile.backend     # Flask API container
├── Dockerfile.frontend    # React app container
├── nginx.conf            # Nginx configuration
├── init-db.py           # Database initialization
├── start.sh             # Startup script
└── stop.sh              # Stop script
```

## 🚦 Different Environments

### Development
```bash
# Run with hot reloading (requires source code mounting)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Production
```bash
# Optimized for production
./start.sh --detached
```

### Testing
```bash
# Run tests in containers
docker-compose exec backend python -m pytest
```

## 🆘 Getting Help

### Check Logs First
```bash
docker-compose logs -f
```

### Common Commands
```bash
# Restart just the backend
docker-compose restart backend

# Update and restart
git pull
./start.sh --build

# View running containers
docker ps

# Access container shell
docker-compose exec backend bash
docker-compose exec frontend sh
```

### Performance Tips

1. **Allocate more memory to Docker:**
   - Docker Desktop: Settings → Resources → Memory (4GB recommended)

2. **Clean up regularly:**
   ```bash
   docker system prune -f
   ```

3. **Monitor resource usage:**
   ```bash
   docker stats
   ```

## 🎉 Success!

Once running, you should see:

- **Frontend:** Modern React interface at http://localhost:3000
- **Backend:** REST API at http://localhost:5000/api
- **Database:** Persistent SQLite database in `../data/`

Start by adding your first coffee product and batch, then track your brewing sessions with detailed tasting notes!

---

*Need help? Check the logs, review this guide, or create an issue in the project repository.*