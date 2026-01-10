#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Create default admin user if not exists
echo "Checking for default admin user..."
python -c "
from app.database import SessionLocal
from app.services.user import UserService
from app.services.password import generate_temp_password

db = SessionLocal()
try:
    service = UserService(db)
    admin = service.get_by_email('admin@labtracker.local')
    if not admin:
        password = generate_temp_password()
        service.create_user(
            email='admin@labtracker.local',
            name='Admin',
            password=password,
            is_admin=True
        )
        print(f'Created admin user: admin@labtracker.local')
        print(f'Temporary password: {password}')
        print('Please change this password after first login!')
    else:
        print('Admin user already exists')
finally:
    db.close()
"

# Start the application
echo "Starting Lab Tracker..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
