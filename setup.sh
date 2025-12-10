#!/bin/bash

echo "🚀 Bedrock Chat Setup Script"
echo "=============================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

echo "✅ Virtual environment created"
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your AWS credentials."
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your AWS credentials before running the app!"
else
    echo "ℹ️  .env file already exists"
fi

echo ""
echo "=============================="
echo "✅ Setup completed successfully!"
echo "=============================="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your AWS credentials"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python app.py"
echo "4. Open: http://localhost:5000"
echo ""
