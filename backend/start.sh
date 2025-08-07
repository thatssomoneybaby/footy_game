#!/bin/bash

# AFL Manager Backend Quick Start Script
set -e

echo "🏈 Starting AFL Manager Backend Setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Poetry is installed
print_status "Checking Poetry installation..."
if ! command -v poetry &> /dev/null; then
    print_error "Poetry not found. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
    print_success "Poetry installed successfully"
else
    print_success "Poetry found"
fi

# Ensure Poetry is in PATH
export PATH="$HOME/.local/bin:$PATH"

# Install dependencies
print_status "Installing Python dependencies..."
poetry install
print_success "Dependencies installed"

# Check if PostgreSQL is running
print_status "Checking PostgreSQL..."
if ! command -v psql &> /dev/null; then
    print_error "PostgreSQL not found. Please install PostgreSQL first."
    print_error "On macOS: brew install postgresql"
    print_error "On Ubuntu: sudo apt-get install postgresql postgresql-contrib"
    exit 1
fi

# Check if PostgreSQL service is running
if ! pg_isready -q; then
    print_warning "PostgreSQL service is not running. Attempting to start..."
    if command -v brew &> /dev/null; then
        brew services start postgresql
    elif command -v systemctl &> /dev/null; then
        sudo systemctl start postgresql
    else
        print_error "Cannot start PostgreSQL automatically. Please start it manually."
        exit 1
    fi
    sleep 2
fi

print_success "PostgreSQL is running"

# Set up environment file
print_status "Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    print_success "Environment file created from template"
    print_warning "Please review and update .env file with your settings"
else
    print_success "Environment file already exists"
fi

# Source environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Create database if it doesn't exist
print_status "Setting up database..."
DB_NAME=${POSTGRES_DB:-afl_manager}
DB_USER=${POSTGRES_USER:-postgres}

# Check if database exists, create if not
if ! psql -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    print_status "Creating database: $DB_NAME"
    createdb -U "$DB_USER" "$DB_NAME"
    print_success "Database created: $DB_NAME"
else
    print_success "Database already exists: $DB_NAME"
fi

# Run migrations
print_status "Running database migrations..."
if [ ! -d "migrations/versions" ] || [ -z "$(ls -A migrations/versions)" ]; then
    print_status "Creating initial migration..."
    poetry run alembic revision --autogenerate -m "Initial schema"
fi

poetry run alembic upgrade head
print_success "Database migrations completed"

# Check if we should seed data
print_status "Checking for seed data..."
if [ -f "seed_data.py" ]; then
    print_status "Running seed data script..."
    poetry run python seed_data.py
    print_success "Seed data loaded"
else
    print_warning "No seed data script found. You may want to add some initial clubs and players."
fi

# Run linting and formatting
print_status "Running code quality checks..."
poetry run ruff check app/ --fix || print_warning "Ruff found some issues"
poetry run black app/ || print_warning "Black formatting applied"
print_success "Code quality checks completed"

# Start the server
print_success "🚀 Setup complete! Starting the server..."
echo ""
echo "📋 Server will be available at:"
echo "   - API: http://localhost:8000"
echo "   - Health Check: http://localhost:8000/health"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the development server
poetry run python run.py