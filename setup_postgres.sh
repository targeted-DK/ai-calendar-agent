#!/bin/bash
# PostgreSQL Setup Script for Life Optimization AI Agent

set -e  # Exit on any error

echo "🔧 Installing PostgreSQL..."
sudo apt update
sudo apt install postgresql postgresql-contrib libpq-dev python3-dev -y

echo "✅ PostgreSQL installed"

echo "🚀 Starting PostgreSQL service..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

echo "📊 Creating database and user..."
# Create database and user
sudo -u postgres psql << EOF
-- Create database
CREATE DATABASE life_optimization;

-- Create user (change password in production!)
CREATE USER life_agent WITH PASSWORD 'secure_password_123';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE life_optimization TO life_agent;

-- Connect to database and grant schema privileges
\c life_optimization
GRANT ALL ON SCHEMA public TO life_agent;

-- Show databases
\l
EOF

echo "✅ Database 'life_optimization' created"
echo "✅ User 'life_agent' created with password 'secure_password_123'"

echo ""
echo "📝 Database connection details:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: life_optimization"
echo "  User: life_agent"
echo "  Password: secure_password_123"
echo ""
echo "Connection string:"
echo "  postgresql://life_agent:secure_password_123@localhost:5432/life_optimization"
echo ""

echo "🧪 Testing connection..."
PGPASSWORD=secure_password_123 psql -h localhost -U life_agent -d life_optimization -c "SELECT version();"

echo ""
echo "✅ PostgreSQL setup complete!"
