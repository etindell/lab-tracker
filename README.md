# Lab Tracker

Web-based project tracking system for research labs. Track projects, experiments, replicates, todos, and notes with a clean, modern interface.

## Features

- **Project Management**: Create and organize research projects with status tracking
- **Experiments**: Manage experiments within projects with multiple status stages
- **Replicates**: Track individual experimental runs with status (planned, in progress, blocked, done)
- **Progress Visualization**: Visual progress bars showing replicate completion across experiments
- **Todo Management**: Create, assign, and track tasks with Kanban board view
- **Notes**: Attach Markdown-formatted notes to experiments and replicates
- **Activity Log**: Track all create/update/archive actions across the system
- **User Management**: Admin interface for managing users with role-based access

## Tech Stack

- **Backend**: FastAPI with Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy 2.0 ORM
- **Migrations**: Alembic
- **Templates**: Jinja2 with Tailwind CSS (via CDN)
- **Interactivity**: HTMX for dynamic updates without full page reloads
- **Authentication**: Session-based auth with bcrypt password hashing

## Quick Start

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 15 or higher

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd lab-tracker
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and secret key
   ```

5. **Set up PostgreSQL database**
   ```bash
   createdb labtracker
   ```

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Create admin user** (optional)
   ```bash
   python -c "
   from app.database import SessionLocal
   from app.services.user import UserService

   db = SessionLocal()
   service = UserService(db)
   service.create_user(
       email='admin@example.com',
       name='Admin',
       password='changeme',
       is_admin=True
   )
   db.close()
   print('Admin user created')
   "
   ```

8. **Start the development server**
   ```bash
   uvicorn app.main:app --reload
   ```

9. **Open** http://localhost:8000 in your browser

### Docker Development

For a quick start with Docker:

```bash
# Start PostgreSQL and the app
docker-compose up -d

# The app will be available at http://localhost:8000
# First run will create an admin user (check logs for credentials)
```

## Configuration

Environment variables (set in `.env` file or system environment):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://localhost:5432/labtracker` |
| `SECRET_KEY` | Session encryption key (change in production!) | `change-me-in-production` |
| `ENVIRONMENT` | `development`, `staging`, or `production` | `development` |
| `DEBUG` | Enable debug mode | `false` |
| `HOST` | Server bind address | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `SESSION_EXPIRE_SECONDS` | Session timeout | `86400` (24 hours) |
| `SESSION_EXPIRE_REMEMBER_SECONDS` | "Remember me" timeout | `2592000` (30 days) |

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_project_service.py

# Run specific test
pytest tests/unit/test_project_service.py::TestProjectService::test_create_project
```

## Deployment

### Railway

1. Connect your GitHub repository to Railway
2. Add a PostgreSQL database service
3. Set environment variables:
   - `DATABASE_URL` (provided by Railway PostgreSQL)
   - `SECRET_KEY` (generate a strong key)
   - `ENVIRONMENT=production`
4. Deploy - the app will automatically run migrations on startup

### Docker

Build and run the production image:

```bash
docker build -t lab-tracker .
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e SECRET_KEY="your-secret-key" \
  -e ENVIRONMENT=production \
  lab-tracker
```

## Project Structure

```
lab-tracker/
├── app/
│   ├── auth/           # Authentication dependencies
│   ├── models/         # SQLAlchemy models
│   ├── routes/         # FastAPI route handlers
│   ├── services/       # Business logic layer
│   ├── config.py       # Configuration management
│   ├── database.py     # Database connection
│   ├── flash.py        # Flash message support
│   └── main.py         # Application entry point
├── alembic/            # Database migrations
├── templates/          # Jinja2 templates
├── static/             # Static files
├── tests/
│   ├── integration/    # API integration tests
│   └── unit/           # Unit tests
├── scripts/
│   └── start.sh        # Production startup script
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── railway.toml
```

## API Documentation

When running in development mode, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT License - see LICENSE file for details.
