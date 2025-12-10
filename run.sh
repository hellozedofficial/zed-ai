#!/bin/bash

echo "🚀 Starting Bedrock Chat Application..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run setup.sh first: ./setup.sh"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and add your AWS credentials"
    exit 1
fi

# Check if AWS credentials are set
if grep -q "your_access_key_here" .env; then
    echo "⚠️  WARNING: Please update your AWS credentials in .env file"
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ Starting Flask server..."
echo ""
python app.py
