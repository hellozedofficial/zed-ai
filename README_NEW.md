# ZED - Professional AI Chat System

A professional AI chat assistant powered by Amazon Bedrock with full user authentication, chat history persistence, and a clean ChatGPT-like interface.

## Features

- User Authentication (Login/Register)
- MySQL Database Integration
- Chat History Persistence
- Multiple AI Models (Claude 3 Sonnet, Haiku, Opus)
- Session Management
- Professional UI/UX
- Secure Password Hashing
- Real-time Chat Interface

## Database Setup

### Database Credentials
```
Host: 127.0.0.1
Port: 3307
Database: zed
Username: root
Password: (empty)
```

### Database Schema

The system uses 3 tables:

1. **users** - User accounts with authentication
2. **chat_sessions** - Chat conversation sessions
3. **messages** - Individual messages in conversations

Tables are automatically created when you run the application.

## Installation

### 1. Install Dependencies

```bash
cd /Users/mac/Documents/AI/ZED
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

The `.env` file is already configured with:
- AWS Bedrock credentials
- Database connection (127.0.0.1:3307)
- Port 3000
- Secret key for sessions

### 3. Initialize Database

```bash
python3 database.py
```

This creates all required tables automatically.

### 4. Start the Application

```bash
python3 app.py
```

Or use the run script:
```bash
./run.sh
```

## Access the Application

Open your browser and navigate to:
```
http://localhost:3000
```

## Usage

### First Time Setup

1. **Register a New Account**
   - Click on "Register" tab
   - Enter username, email, and password (min 6 characters)
   - Click "Create Account"

2. **Login**
   - Enter your username or email
   - Enter your password
   - Click "Login"

### Using the Chat Interface

1. **Start a New Chat**
   - Click the "New Chat" button in the sidebar
   - Or simply start typing in the message box

2. **Send Messages**
   - Type your message in the input box
   - Press Enter or click the send button
   - AI will respond in real-time

3. **Switch Between Chats**
   - All your previous conversations appear in the left sidebar
   - Click on any conversation to load it
   - Messages are persisted in the database

4. **Delete Conversations**
   - Hover over a conversation in the sidebar
   - Click the delete icon
   - Confirm deletion

5. **Change AI Model**
   - Use the model selector in the top-right
   - Choose between Claude 3 Sonnet, Haiku, or Opus

## API Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - Login user
- `POST /api/logout` - Logout current user
- `GET /api/user` - Get current user info

### Chat Operations
- `POST /api/chat` - Send message and get AI response
- `GET /api/sessions` - Get all user's chat sessions
- `GET /api/sessions/<id>` - Get specific session with messages
- `DELETE /api/sessions/<id>` - Delete a chat session

### General
- `GET /api/models` - List available AI models
- `GET /api/health` - Health check

## Project Structure

```
ZED/
├── app.py                      # Main Flask application
├── database.py                 # Database connection and schema
├── requirements.txt            # Python dependencies
├── .env                        # Environment configuration
├── templates/
│   ├── auth.html              # Login/Register page
│   └── chat.html              # Chat interface
└── static/
    ├── chat-style.css         # Chat page styles
    └── chat-script.js         # Chat functionality
```

## Security Features

- Password hashing with bcrypt
- Session-based authentication with Flask-Login
- SQL injection prevention with parameterized queries
- CSRF protection
- Secure session cookies
- User-specific data isolation

## Database Configuration

The application connects to MySQL with these settings:
```python
Host: 127.0.0.1
Port: 3307
Database: zed
User: root
Password: '' (empty)
```

All tables use InnoDB engine with UTF-8MB4 character set for full Unicode support.

## Troubleshooting

### Port Already in Use
```bash
lsof -ti:3000 | xargs kill -9
```

### Database Connection Error
- Ensure MySQL is running on port 3307
- Verify the 'zed' database exists
- Check credentials in .env file

### Module Not Found
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: MySQL with PyMySQL
- **Authentication**: Flask-Login + bcrypt
- **AI**: Amazon Bedrock (Claude 3)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3

## Production Deployment

For production use:

1. Change SECRET_KEY in .env
2. Set FLASK_DEBUG=False
3. Use a production WSGI server (gunicorn)
4. Enable HTTPS
5. Use environment variables for sensitive data
6. Set up proper database backups

## Support

For issues or questions, check the application logs or review the code comments.

---

**Powered by HelloZed**
Built with Amazon Bedrock and Flask
