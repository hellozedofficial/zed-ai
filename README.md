# Bedrock Chat - ChatGPT Clone

Amazon Bedrock ব্যবহার করে তৈরি একটি সম্পূর্ণ ChatGPT-এর মতো চ্যাট সিস্টেম। এটি Flask ব্যাকএন্ড এবং আধুনিক ওয়েব ফ্রন্টএন্ড দিয়ে তৈরি।

## ✨ বৈশিষ্ট্যসমূহ

### Core Features
- 💬 **রিয়েল-টাইম চ্যাট**: ChatGPT-এর মতো সুন্দর ইন্টারফেস
- 🤖 **Multiple AI Models**: Claude 3 Sonnet, Haiku, Opus সাপোর্ট
- 🌐 **বাংলা ভাষা সাপোর্ট**: সম্পূর্ণ বাংলায় ব্যবহার করা যায়
- 📝 **Conversation History**: চ্যাট হিস্টোরি সংরক্ষণ ও Export
- 🎨 **Modern UI/UX**: সুন্দর এবং রেসপন্সিভ ডিজাইন
- ⚡ **Fast & Reliable**: AWS Bedrock-এর শক্তিশালী সুবিধা

### Enhanced Features
- 🔒 **Security**: Input validation, rate limiting, এবং comprehensive error handling
- 🚀 **Performance**: Request timeout, retry logic, এবং optimized loading states
- ⌨️ **Keyboard Shortcuts**: Ctrl+Enter (send), Ctrl+K (new chat)
- 📤 **Export Functionality**: Conversation export as text file
- 🛡️ **Error Recovery**: Enhanced error messages with retry capabilities
- 💾 **Auto-Save**: Automatic conversation persistence in browser

## 🚀 ইনস্টলেশন

### প্রয়োজনীয়তা

- Python 3.8 বা তার উপরের ভার্সন
- AWS Account এবং Bedrock Access
- AWS Access Key এবং Secret Key

### ধাপসমূহ

1. **Repository ক্লোন করুন:**
```bash
git clone <your-repo-url>
cd ZED
```

2. **Virtual Environment তৈরি করুন:**
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# অথবা
venv\Scripts\activate  # Windows
```

3. **Dependencies ইনস্টল করুন:**
```bash
pip install -r requirements.txt
```

4. **Environment Variables সেটআপ করুন:**
```bash
cp .env.example .env
```

এরপর `.env` ফাইলটি এডিট করে আপনার AWS credentials যোগ করুন:
```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1

# Bedrock Model Configuration
BEDROCK_MODEL_ID=amazon.nova-pro-v1:0

# Flask Configuration
SECRET_KEY=your-secret-key-change-in-production
PORT=5000
FLASK_DEBUG=False

# Security Configuration (Optional)
ALLOWED_ORIGINS=*
MAX_MESSAGE_LENGTH=4000
MAX_HISTORY_LENGTH=20
RATE_LIMIT_PER_MINUTE=10
REQUEST_TIMEOUT=30
```

5. **অ্যাপ্লিকেশন চালু করুন:**
```bash
python app.py
```

6. **ব্রাউজারে খুলুন:**
```
http://localhost:5000
```

## 🔧 Configuration

### AWS Bedrock Setup

1. AWS Console-এ লগইন করুন
2. Bedrock সার্ভিস-এ যান
3. Model Access সক্রিয় করুন:
   - Anthropic Claude মডেলগুলো enable করুন
   - অনুমতি পেতে ২৪-৪৮ ঘণ্টা সময় লাগতে পারে

4. IAM User তৈরি করুন:
   - Bedrock permissions সহ
   - Access Key এবং Secret Key জেনারেট করুন

### Available Models

- **Claude 3 Sonnet** (সুপারিশকৃত): দ্রুত এবং কার্যকর
- **Claude 3 Haiku**: দ্রুততম এবং সাশ্রয়ী
- **Claude 3 Opus**: সবচেয়ে শক্তিশালী
- **Claude 2.1**: পুরানো কিন্তু স্থিতিশীল
- **Llama 3 70B**: Meta-এর ওপেন সোর্স মডেল

## 📁 প্রজেক্ট স্ট্রাকচার

```
ZED/
├── app.py                 # Flask backend server
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore           # Git ignore rules
├── README.md            # Project documentation
├── SECURITY.md          # Security features and guidelines
├── templates/
│   └── index.html       # Main HTML template
└── static/
    ├── style.css        # CSS styles
    └── script.js        # JavaScript code
```

## 🎯 ব্যবহার

### Basic Usage
1. **নতুন চ্যাট শুরু করুন**: "নতুন চ্যাট" বাটনে ক্লিক করুন
2. **মডেল নির্বাচন করুন**: সাইডবার থেকে আপনার পছন্দের AI মডেল বেছে নিন
3. **প্রশ্ন করুন**: টেক্সট বক্সে আপনার প্রশ্ন লিখুন এবং Send করুন
4. **উত্তর পান**: AI আপনাকে তাৎক্ষণিক উত্তর দেবে

### Advanced Features
- **Keyboard Shortcuts**:
  - `Ctrl + Enter`: Message send করুন
  - `Ctrl + K`: নতুন chat শুরু করুন
  - `Escape`: Input field-এ focus করুন
- **Export Chat**: সাইডবার থেকে "Export Chat" বাটনে ক্লিক করে conversation টি text file হিসেবে download করুন
- **Auto-save**: আপনার conversation automatically browser-এ save হয়ে থাকে
- **Error Recovery**: Error হলে "Retry" বাটন দিয়ে আবার চেষ্টা করুন

## 🛠️ API Endpoints

### POST `/api/chat`
চ্যাট মেসেজ পাঠান এবং AI-এর উত্তর পান।

**Request Body:**
```json
{
  "message": "আপনার প্রশ্ন",
  "history": [],
  "model": "amazon.nova-pro-v1:0"
}
```

**Response:**
```json
{
  "response": "AI-এর উত্তর",
  "model": "amazon.nova-pro-v1:0"
}
```

### GET `/api/models`
উপলব্ধ AI মডেলগুলোর তালিকা পান।

### GET `/api/health`
সার্ভার স্বাস্থ্য পরীক্ষা করুন।

## 🔒 Security

### Built-in Security Features
- ✅ **Input Validation**: Message length এবং format validation
- ✅ **Rate Limiting**: IP-based request limiting (default: 10/minute)
- ✅ **Error Handling**: Secure error messages without sensitive data exposure
- ✅ **Request Validation**: JSON validation এবং timeout handling
- ✅ **XSS Protection**: HTML escaping for user content
- ✅ **AWS Security**: Proper credential handling এবং error mapping

### Security Best Practices
- **কখনোই** `.env` ফাইল Git-এ কমিট করবেন না
- AWS credentials নিরাপদে রাখুন
- Production-এ HTTPS ব্যবহার করুন
- Strong secret key ব্যবহার করুন
- CORS origins properly configure করুন

📋 **Detailed Security Documentation**: [`SECURITY.md`](SECURITY.md) দেখুন

## 💰 খরচ

AWS Bedrock-এর খরচ মডেল অনুযায়ী:
- Input tokens: প্রতি ১০০০ টোকেনে $০.০০৩ - $০.০১৫
- Output tokens: প্রতি ১০০০ টোকেনে $০.০১৫ - $০.০৭৫

Free tier উপলব্ধ নেই, তবে pay-as-you-go মডেল।

## 🐛 সমস্যা সমাধান

### "Access Denied" Error
- AWS credentials সঠিক আছে কিনা চেক করুন
- Bedrock model access সক্রিয় করেছেন কিনা নিশ্চিত করুন
- IAM permissions সঠিক আছে কিনা দেখুন

### Connection Error
- ইন্টারনেট সংযোগ চেক করুন
- AWS region সঠিক আছে কিনা দেখুন
- Firewall settings চেক করুন

### Model Not Available
- নির্দিষ্ট মডেল আপনার region-এ উপলব্ধ কিনা চেক করুন
- Model access request approved হয়েছে কিনা দেখুন

## 🤝 অবদান

Pull requests স্বাগতম! বড় পরিবর্তনের জন্য, প্রথমে একটি issue খুলে আলোচনা করুন।

## 📝 License

MIT License - আপনি স্বাধীনভাবে ব্যবহার, পরিবর্তন এবং বিতরণ করতে পারেন।

## 🙏 স্বীকৃতি

- [Amazon Bedrock](https://aws.amazon.com/bedrock/) - AI মডেল প্রদানের জন্য
- [Anthropic Claude](https://www.anthropic.com/) - শক্তিশালী language model-এর জন্য
- [Flask](https://flask.palletsprojects.com/) - ওয়েব ফ্রেমওয়ার্কের জন্য

## 📧 যোগাযোগ

প্রশ্ন বা সহায়তার জন্য, issue খুলুন অথবা ইমেইল করুন।

---

**তৈরি করেছেন ❤️ দিয়ে এবং AWS Bedrock দিয়ে**
# zed-ai
