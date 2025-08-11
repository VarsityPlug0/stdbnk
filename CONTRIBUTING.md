# Contributing to Standard Bank Verification App

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## How to Contribute

### 1. Fork the Repository
```bash
git fork https://github.com/yourusername/stdbnk.git
```

### 2. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 3. Make Your Changes
- Write clean, well-documented code
- Follow Python PEP 8 style guidelines
- Add comments explaining complex logic
- Test your changes thoroughly

### 4. Commit Your Changes
```bash
git add .
git commit -m "Add: Brief description of your feature"
```

### 5. Push to Your Fork
```bash
git push origin feature/your-feature-name
```

### 6. Submit a Pull Request
- Provide a clear description of your changes
- Include screenshots if UI changes are involved
- Reference any related issues

## Development Setup

### Local Development
```bash
# Clone your fork
git clone https://github.com/yourusername/stdbnk.git
cd stdbnk

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

### Docker Development
```bash
# Build and run with Docker
docker-compose up -d

# View logs
docker-compose logs -f
```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions small and focused
- Add comments for complex logic

## Testing

Before submitting a pull request:

1. Test the main form submission
2. Test admin login/logout
3. Test admin dashboard functionality
4. Verify mobile responsiveness
5. Check for any console errors

## Security Considerations

When contributing:

- Never commit sensitive data (passwords, keys, etc.)
- Validate all user inputs
- Use parameterized queries for database operations
- Follow secure coding practices

## Questions?

If you have questions, please:

1. Check existing issues first
2. Create a new issue with your question
3. Be specific about what you're trying to achieve

## Types of Contributions We Welcome

- 🐛 Bug fixes
- ✨ New features
- 📚 Documentation improvements
- 🎨 UI/UX enhancements
- 🔒 Security improvements
- 🚀 Performance optimizations
- 🧪 Test coverage improvements

Thank you for contributing! 🎉
