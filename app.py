from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import boto3
import json
import os
import logging
import bcrypt
import re
import requests
import sys
import subprocess
import tempfile
from io import StringIO
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv
from database import get_db_connection, init_database, generate_share_hash
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Security configurations
app.config.update(
    SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key-change-in-production'),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    JSON_AS_ASCII=False,
    PERMANENT_SESSION_LIFETIME=timedelta(days=7)
)

CORS(app, supports_credentials=True)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username, email FROM users WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            if user_data:
                return User(user_data['id'], user_data['username'], user_data['email'])
    finally:
        connection.close()
    return None

# Initialize AWS Bedrock client
try:
    bedrock_runtime = boto3.client(
        service_name='bedrock-runtime',
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    logger.info("AWS Bedrock client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize AWS Bedrock client: {e}")
    bedrock_runtime = None

MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'amazon.nova-pro-v1:0')

# Google Custom Search setup
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

def needs_web_search(message: str) -> bool:
    """Detect if a message requires web search"""
    search_keywords = [
        'latest', 'recent', 'current', 'today', 'now', 'news',
        'what is happening', 'what happened', 'update on',
        'weather', 'stock', 'price', 'score', 'result',
        'search for', 'find', 'look up', 'who is', 'what is', 'whats', "what's", 'when is', 'where is', 'how to',
        'define', 'definition', 'wiki', 'wikipedia', 'google', 'bing', 'yahoo'
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in search_keywords)

def perform_web_search(query: str, num_results: int = 5) -> List[Dict]:
    """Perform Google Custom Search and return results"""
    if not GOOGLE_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
        logger.warning("Google API credentials not configured")
        return []
    
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        result = service.cse().list(
            q=query,
            cx=GOOGLE_SEARCH_ENGINE_ID,
            num=num_results
        ).execute()
        
        search_results = []
        if 'items' in result:
            for item in result['items']:
                search_results.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', '')
                })
        
        logger.info(f"Found {len(search_results)} search results for: {query}")
        return search_results
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return []

def format_search_context(search_results: List[Dict]) -> str:
    """Format search results into context for AI model"""
    if not search_results:
        return ""
    
    context = "\n\n[Web Search Results]:\n"
    for i, result in enumerate(search_results, 1):
        context += f"\n{i}. {result['title']}\n"
        context += f"   Source: {result['link']}\n"
        context += f"   {result['snippet']}\n"
    
    context += "\n[End of Search Results]\n"
    context += "Please use the above search results to provide accurate and up-to-date information in your response.\n\n"
    return context

# Routes
@app.route('/')
def index():
    """Serve the main page"""
    if current_user.is_authenticated:
        return render_template('chat.html')
    return render_template('auth.html')

@app.route('/chat')
@login_required
def chat_page():
    """Serve the chat interface"""
    return render_template('chat.html')

@app.route('/c/<string:share_hash>')
def load_chat(share_hash):
    """Load a specific chat session by share hash"""
    if not current_user.is_authenticated:
        # Store the intended destination and redirect to login
        session['next'] = f'/c/{share_hash}'
        return redirect(url_for('index'))
    
    # Verify the session belongs to the current user
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, user_id, share_hash FROM chat_sessions WHERE share_hash = %s",
                (share_hash,)
            )
            session_data = cursor.fetchone()
            
            if not session_data:
                return redirect(url_for('index'))  # Session not found
            
            if session_data['user_id'] != current_user.id:
                return redirect(url_for('index'))  # Not the owner
            
            # Session is valid, render chat with share_hash parameter
            return render_template('chat.html', share_hash=share_hash, session_id=session_data['id'])
    finally:
        connection.close()

# Authentication endpoints
@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validation
        if not username or len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        if not email or '@' not in email:
            return jsonify({'error': 'Valid email is required'}), 400
        if not password or len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Check if username or email exists
                cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
                if cursor.fetchone():
                    return jsonify({'error': 'Username or email already exists'}), 400
                
                # Insert new user
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    (username, email, password_hash)
                )
                connection.commit()
                user_id = cursor.lastrowid
                
                # Log in the user
                user = User(user_id, username, email)
                login_user(user, remember=True)
                
                return jsonify({
                    'success': True,
                    'user': {
                        'id': user_id,
                        'username': username,
                        'email': email
                    }
                })
        finally:
            connection.close()
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Log in a user"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Find user
                cursor.execute(
                    "SELECT id, username, email, password_hash FROM users WHERE username = %s OR email = %s",
                    (username, username)
                )
                user_data = cursor.fetchone()
                
                if not user_data:
                    return jsonify({'error': 'Invalid username or password'}), 401
                
                # Verify password
                if not bcrypt.checkpw(password.encode('utf-8'), user_data['password_hash'].encode('utf-8')):
                    return jsonify({'error': 'Invalid username or password'}), 401
                
                # Update last login
                cursor.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user_data['id'],))
                connection.commit()
                
                # Log in the user
                user = User(user_data['id'], user_data['username'], user_data['email'])
                login_user(user, remember=True)
                
                return jsonify({
                    'success': True,
                    'user': {
                        'id': user_data['id'],
                        'username': user_data['username'],
                        'email': user_data['email']
                    }
                })
        finally:
            connection.close()
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    """Log out the current user"""
    logout_user()
    return jsonify({'success': True})

@app.route('/api/user', methods=['GET'])
@login_required
def get_user():
    """Get current user info"""
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email
    })

# Chat endpoints
@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """Handle chat requests"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        model_id = data.get('model', MODEL_ID)
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Create new session if needed
                if not session_id:
                    title = user_message[:50] + ('...' if len(user_message) > 50 else '')
                    share_hash = generate_share_hash()
                    cursor.execute(
                        "INSERT INTO chat_sessions (user_id, title, model_id, share_hash) VALUES (%s, %s, %s, %s)",
                        (current_user.id, title, model_id, share_hash)
                    )
                    connection.commit()
                    session_id = cursor.lastrowid
                else:
                    # Verify session belongs to user
                    cursor.execute(
                        "SELECT id FROM chat_sessions WHERE id = %s AND user_id = %s",
                        (session_id, current_user.id)
                    )
                    if not cursor.fetchone():
                        return jsonify({'error': 'Invalid session'}), 403
                
                # Get conversation history
                cursor.execute(
                    "SELECT role, content FROM messages WHERE session_id = %s ORDER BY created_at ASC",
                    (session_id,)
                )
                history = cursor.fetchall()
                
                # Save user message
                cursor.execute(
                    "INSERT INTO messages (session_id, role, content) VALUES (%s, %s, %s)",
                    (session_id, 'user', user_message)
                )
                connection.commit()
                
                # Check if web search is needed
                search_context = ""
                if needs_web_search(user_message):
                    logger.info(f"Web search triggered for: {user_message}")
                    search_results = perform_web_search(user_message)
                    if search_results:
                        search_context = format_search_context(search_results)
                
                # Prepare messages for Bedrock
                messages = []
                
                # Add system message for better behavior (only for first message in conversation)
                if not history:
                    system_message = (
                        "You are ZED, a friendly AI assistant. "
                        "Respond naturally in the user's language. "
                        "Be brief and direct - answer like a human in casual chat. "
                        "Never show thinking process or translate unless asked. "
                        "Example: User asks 'I love you mane ki?' → Just say 'আমি তোমাকে ভালোবাসি' - that's it!"
                    )
                    messages.append({
                        'role': 'user',
                        'content': system_message
                    })
                    messages.append({
                        'role': 'assistant',
                        'content': 'Got it! Short, natural answers only.'
                    })
                
                for msg in history:
                    messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
                
                # Add search context to user message if available
                final_user_message = search_context + user_message if search_context else user_message
                
                messages.append({
                    'role': 'user',
                    'content': final_user_message
                })
                
                # Prepare request body based on model type
                try:
                    if 'anthropic.claude' in model_id:
                        # Claude format (Anthropic models) with system prompt
                        request_body = { 
                            'anthropic_version': 'bedrock-2023-05-31',
                            'max_tokens': 4096,
                            'messages': messages,
                            'temperature': 0.7,
                            'top_p': 0.9,
                            'system': (
                                "You are ZED, a helpful AI assistant. "
                                "Always respond directly and concisely in the same language as the user's question. "
                                "Never show your thinking process, reasoning steps, or provide translations. "
                                "Give short, natural answers - like a human would in casual conversation. "
                                "If asked in Arabic, respond only in Arabic. "
                                "If asked in Bengali, respond only in Bengali. "
                                "If asked in English, respond only in English. "
                                "Be brief unless the user asks for detailed explanation. "
                                "Avoid unnecessary elaboration or multiple explanations."
                            )
                        }
                    elif 'amazon.nova' in model_id or 'meta.llama' in model_id or 'mistral.' in model_id or 'cohere.' in model_id or 'ai21.' in model_id or 'qwen.' in model_id or 'minimax.' in model_id or 'moonshot.' in model_id or 'deepseek.' in model_id:
                        # Nova, Llama, Mistral, Cohere, and other models use inferenceConfig format
                        request_body = {
                            'messages': messages,
                            'inferenceConfig': {
                                'maxTokens': 4096,
                                'temperature': 0.7,
                                'topP': 0.9
                            }
                        }
                    elif 'openai.gpt' in model_id or 'google.gemma' in model_id:
                        # OpenAI and Google Gemma format
                        request_body = {
                            'messages': messages,
                            'max_tokens': 4096,
                            'temperature': 0.7,
                            'top_p': 0.9
                        }
                    else:
                        # Default format - try inferenceConfig
                        request_body = {
                            'messages': messages,
                            'inferenceConfig': {
                                'maxTokens': 4096,
                                'temperature': 0.7,
                                'topP': 0.9
                            }
                        }
                    
                    logger.info(f"Calling Bedrock - Model: {model_id}")
                    logger.info(f"Request: {json.dumps(request_body, indent=2)}")
                    
                    response = bedrock_runtime.invoke_model(
                        modelId=model_id,
                        body=json.dumps(request_body)
                    )
                    
                    response_body = json.loads(response['body'].read())
                    logger.info(f"Response: {json.dumps(response_body, indent=2)}")
                    
                    # Parse response based on model type
                    if 'anthropic.claude' in model_id:
                        # Claude format response
                        assistant_message = response_body['content'][0]['text']
                    elif 'openai.gpt' in model_id or 'google.gemma' in model_id:
                        # OpenAI/Gemma format response
                        assistant_message = response_body['choices'][0]['message']['content']
                    elif 'output' in response_body and 'message' in response_body['output']:
                        # Nova, Llama, Mistral format response
                        assistant_message = response_body['output']['message']['content'][0]['text']
                    elif 'content' in response_body:
                        # Alternative format
                        if isinstance(response_body['content'], list):
                            assistant_message = response_body['content'][0].get('text', str(response_body['content'][0]))
                        else:
                            assistant_message = response_body['content']
                    else:
                        # Fallback - try to extract any text content
                        assistant_message = str(response_body)
                        
                except Exception as bedrock_error:
                    logger.error(f"Bedrock API error: {str(bedrock_error)}")
                    logger.error(f"Error type: {type(bedrock_error).__name__}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    raise bedrock_error
                
                # Save assistant message
                cursor.execute(
                    "INSERT INTO messages (session_id, role, content) VALUES (%s, %s, %s)",
                    (session_id, 'assistant', assistant_message)
                )
                connection.commit()
                
                return jsonify({
                    'response': assistant_message,
                    'session_id': session_id,
                    'model': model_id
                })
                
        finally:
            connection.close()
            
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions', methods=['GET'])
@login_required
def get_sessions():
    """Get user's chat sessions"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT id, share_hash, title, model_id, created_at, updated_at 
                   FROM chat_sessions 
                   WHERE user_id = %s 
                   ORDER BY updated_at DESC 
                   LIMIT 50""",
                (current_user.id,)
            )
            sessions = cursor.fetchall()
            
            # Format dates
            for session in sessions:
                session['created_at'] = session['created_at'].isoformat() if session['created_at'] else None
                session['updated_at'] = session['updated_at'].isoformat() if session['updated_at'] else None
            
            return jsonify(sessions)
    finally:
        connection.close()

@app.route('/api/sessions/<int:session_id>', methods=['GET'])
@login_required
def get_session(session_id):
    """Get a specific session with messages"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Verify session belongs to user
            cursor.execute(
                "SELECT id, title, model_id, created_at FROM chat_sessions WHERE id = %s AND user_id = %s",
                (session_id, current_user.id)
            )
            session = cursor.fetchone()
            
            if not session:
                return jsonify({'error': 'Session not found'}), 404
            
            # Get messages
            cursor.execute(
                "SELECT role, content, created_at FROM messages WHERE session_id = %s ORDER BY created_at ASC",
                (session_id,)
            )
            messages = cursor.fetchall()
            
            # Format dates
            session['created_at'] = session['created_at'].isoformat() if session['created_at'] else None
            for msg in messages:
                msg['created_at'] = msg['created_at'].isoformat() if msg['created_at'] else None
            
            return jsonify({
                'session': session,
                'messages': messages
            })
    finally:
        connection.close()

@app.route('/api/sessions/<int:session_id>', methods=['DELETE'])
@login_required
def delete_session(session_id):
    """Delete a chat session"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM chat_sessions WHERE id = %s AND user_id = %s",
                (session_id, current_user.id)
            )
            connection.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Session not found'}), 404
            
            return jsonify({'success': True})
    finally:
        connection.close()

@app.route('/api/execute-code', methods=['POST'])
@login_required
def execute_code():
    """Execute Python or JavaScript code in a sandboxed environment"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        language = data.get('language', 'python').lower()
        
        if not code:
            return jsonify({'error': 'Code is required'}), 400
        
        # Security: Limit execution time and resource usage
        timeout = 5  # seconds
        
        if language == 'python':
            result = execute_python_code(code, timeout)
        elif language == 'javascript':
            result = execute_javascript_code(code, timeout)
        else:
            return jsonify({'error': f'Unsupported language: {language}'}), 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Code execution error: {e}")
        return jsonify({'error': str(e)}), 500

def execute_python_code(code: str, timeout: int) -> Dict:
    """Execute Python code and capture output"""
    try:
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute with timeout
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = result.stdout
            error = result.stderr
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'output': output or 'Code executed successfully with no output',
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'output': output,
                    'error': error or 'Execution failed'
                }
        finally:
            # Clean up temp file
            os.unlink(temp_file)
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': None,
            'error': f'Execution timeout after {timeout} seconds'
        }
    except Exception as e:
        return {
            'success': False,
            'output': None,
            'error': str(e)
        }

def execute_javascript_code(code: str, timeout: int) -> Dict:
    """Execute JavaScript code using Node.js"""
    try:
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Check if Node.js is available
            result = subprocess.run(
                ['node', temp_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = result.stdout
            error = result.stderr
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'output': output or 'Code executed successfully with no output',
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'output': output,
                    'error': error or 'Execution failed'
                }
        finally:
            # Clean up temp file
            os.unlink(temp_file)
            
    except FileNotFoundError:
        return {
            'success': False,
            'output': None,
            'error': 'Node.js is not installed. JavaScript execution requires Node.js.'
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': None,
            'error': f'Execution timeout after {timeout} seconds'
        }
    except Exception as e:
        return {
            'success': False,
            'output': None,
            'error': str(e)
        }

@app.route('/api/models', methods=['GET'])
def get_models():
    """Return available Bedrock models"""
    models = [
        # Claude Models
        {'id': 'anthropic.claude-3-haiku-20240307-v1:0', 'name': 'Claude 3 Haiku (Default)', 'provider': 'Anthropic'},
        
        # Amazon Nova Models
        {'id': 'amazon.nova-premier-v1:0', 'name': 'Nova Premier', 'provider': 'Amazon'},
        {'id': 'amazon.nova-pro-v1:0', 'name': 'Nova Pro', 'provider': 'Amazon'},
        {'id': 'amazon.nova-2-sonic-v1:0', 'name': 'Nova 2 Sonic', 'provider': 'Amazon'},
        {'id': 'amazon.nova-2-lite-v1:0', 'name': 'Nova 2 Lite', 'provider': 'Amazon'},
        {'id': 'amazon.nova-sonic-v1:0', 'name': 'Nova Sonic', 'provider': 'Amazon'},
        {'id': 'amazon.nova-lite-v1:0', 'name': 'Nova Lite', 'provider': 'Amazon'},
        {'id': 'amazon.nova-micro-v1:0', 'name': 'Nova Micro', 'provider': 'Amazon'},
        
        # Meta Llama Models
        {'id': 'meta.llama4-scout-405b-v1:0', 'name': 'Llama 4 Scout 405B', 'provider': 'Meta'},
        {'id': 'meta.llama4-maverick-v1:0', 'name': 'Llama 4 Maverick', 'provider': 'Meta'},
        {'id': 'meta.llama3-3-70b-instruct-v1:0', 'name': 'Llama 3.3 70B Instruct', 'provider': 'Meta'},
        {'id': 'meta.llama3-2-90b-instruct-v1:0', 'name': 'Llama 3.2 90B Instruct', 'provider': 'Meta'},
        {'id': 'meta.llama3-1-70b-instruct-v1:0', 'name': 'Llama 3.1 70B Instruct', 'provider': 'Meta'},
        
        # Mistral Models
        {'id': 'mistral.mistral-large-3-2503-v1:0', 'name': 'Mistral Large 3', 'provider': 'Mistral'},
        {'id': 'mistral.magistral-large-2407-v1:0', 'name': 'Magistral Large 2407', 'provider': 'Mistral'},
        {'id': 'mistral.ministral-3b-2410-v1:0', 'name': 'Ministral 3B 2410', 'provider': 'Mistral'},
        {'id': 'mistral.mixtral-8x7b-instruct-v0:1', 'name': 'Mixtral 8x7B Instruct', 'provider': 'Mistral'},
        
        # DeepSeek Model
        {'id': 'deepseek.deepseek-r1-distill-qwen-32b-v1:0', 'name': 'DeepSeek R1 Distill Qwen 32B', 'provider': 'DeepSeek'},
        
        # Cohere Models
        {'id': 'cohere.command-r-plus-v1:0', 'name': 'Command R+', 'provider': 'Cohere'},
        {'id': 'cohere.command-r-v1:0', 'name': 'Command R', 'provider': 'Cohere'},
        
        # OpenAI Models
        {'id': 'openai.gpt-oss-120b-1:0', 'name': 'GPT OSS 120B', 'provider': 'OpenAI'},
        {'id': 'openai.gpt-oss-20b-1:0', 'name': 'GPT OSS 20B', 'provider': 'OpenAI'},
        
        # AI21 Labs Models
        {'id': 'ai21.jamba-2-ultra-v1:0', 'name': 'Jamba 2 Ultra', 'provider': 'AI21 Labs'},
        {'id': 'ai21.jamba-2-large-v1:0', 'name': 'Jamba 2 Large', 'provider': 'AI21 Labs'},
        
        # Google Models
        {'id': 'google.gemma-3-27b-it-v1:0', 'name': 'Gemma 3 27B IT', 'provider': 'Google'},
        {'id': 'google.gemma-3-9b-it-v1:0', 'name': 'Gemma 3 9B IT', 'provider': 'Google'},
        
        # Qwen Models
        {'id': 'qwen.qwen3-next-70b-instruct-v1:0', 'name': 'Qwen3 Next 70B Instruct', 'provider': 'Qwen'},
        {'id': 'qwen.qwen2-5-32b-instruct-v1:0', 'name': 'Qwen 2.5 32B Instruct', 'provider': 'Qwen'},
        {'id': 'qwen.qwq-32b-preview-v1:0', 'name': 'QwQ 32B Preview', 'provider': 'Qwen'},
        
        # MiniMax Model
        {'id': 'minimax.minimax-m2-v1:0', 'name': 'MiniMax M2', 'provider': 'MiniMax'},
        
        # Moonshot Model
        {'id': 'moonshot.moonshot-kimi-k2-v1:0', 'name': 'Moonshot Kimi K2', 'provider': 'Moonshot'}
    ]
    return jsonify(models)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'ZED Chat'})

if __name__ == '__main__':
    # Initialize database
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    port = int(os.getenv('PORT', 3000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
