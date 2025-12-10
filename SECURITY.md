# Security Features

This document outlines the security measures implemented in the Bedrock Chat application.

## 🔒 Security Improvements Implemented

### 1. **Input Validation & Sanitization**
- **Message Length Limits**: Maximum 4,000 characters per message
- **History Length Limits**: Maximum 20 messages in conversation history
- **Model Validation**: Only allowed models can be used
- **JSON Validation**: Proper JSON parsing with error handling
- **HTML Escaping**: All user content is properly escaped to prevent XSS

### 2. **Rate Limiting**
- **Per-IP Rate Limiting**: Default 10 requests per minute per IP
- **Configurable Limits**: Adjustable via environment variables
- **Memory-based Store**: Simple in-memory rate limiting (suitable for single-instance deployment)

### 3. **Error Handling & Logging**
- **Comprehensive Logging**: All requests, errors, and performance metrics logged
- **Structured Error Responses**: Consistent error format with appropriate HTTP status codes
- **AWS Error Mapping**: Specific handling for different AWS Bedrock error types
- **No Sensitive Data Exposure**: Error messages don't expose internal details

### 4. **Request Security**
- **Request Size Limits**: Maximum 16MB request payload
- **Request Timeouts**: Configurable timeout (default 30 seconds)
- **CORS Configuration**: Configurable allowed origins
- **Content Type Validation**: Only accepts JSON requests

### 5. **AWS Configuration Security**
- **Credential Management**: Secure handling of AWS credentials via environment variables
- **Connection Pooling**: Proper AWS client configuration with retries
- **Region Configuration**: Configurable AWS region
- **Access Control**: Validates AWS permissions before processing

## 🛡️ Configuration

### Environment Variables

```bash
# Security Settings
SECRET_KEY=your-secret-key-change-in-production
ALLOWED_ORIGINS=https://yourdomain.com,https://anotherdomain.com
MAX_MESSAGE_LENGTH=4000
MAX_HISTORY_LENGTH=20
RATE_LIMIT_PER_MINUTE=10
REQUEST_TIMEOUT=30

# AWS Security
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key_here
AWS_REGION=us-east-1
```

### Production Recommendations

1. **Use HTTPS**: Always deploy with TLS/SSL in production
2. **Secure Secret Key**: Generate a strong, random secret key
3. **Restrict CORS**: Set specific allowed origins instead of `*`
4. **Monitor Rate Limits**: Implement more sophisticated rate limiting for high-traffic scenarios
5. **Log Analysis**: Monitor logs for suspicious activity
6. **AWS IAM**: Use minimal necessary permissions for the AWS user
7. **Environment Isolation**: Use separate AWS accounts/regions for development and production

## 🚨 Security Checklist

- [x] Input validation and sanitization
- [x] Rate limiting implementation
- [x] Error handling without information disclosure
- [x] Secure credential management
- [x] Request size and timeout limits
- [x] CORS configuration
- [x] Comprehensive logging
- [x] XSS prevention through HTML escaping
- [x] AWS error handling
- [x] Model validation

## ⚠️ Known Limitations

1. **In-Memory Rate Limiting**: Current implementation uses memory-based rate limiting, which doesn't persist across restarts or scale across multiple instances
2. **No Authentication**: Application doesn't include user authentication (add as needed)
3. **No Request Signing**: Requests to the application aren't signed (consider adding HMAC or similar)

## 🔧 Future Security Enhancements

- Implement Redis-based rate limiting for scalability
- Add user authentication and authorization
- Implement request signing/verification
- Add more sophisticated input filtering
- Implement session management
- Add audit logging
- Consider implementing CSRF protection for web forms