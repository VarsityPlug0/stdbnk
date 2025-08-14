# User Activity Tracking System

This Flask application now includes a comprehensive user activity tracking system that monitors user interactions and provides detailed analytics through an admin interface.

## 🚀 Features

### 1. **Automatic Activity Tracking**
- **Page Visits**: Automatically logged when users navigate to any page
- **Button Clicks**: Tracks clicks on buttons, links, and interactive elements
- **Form Submissions**: Monitors all form submissions with success/failure status
- **Input Focus**: Records when users focus on input fields

### 2. **Comprehensive Data Collection**
- User session identification (anonymous but persistent)
- IP address tracking
- User agent (browser) information
- Timestamp with precise timing
- Page/endpoint information
- Element identification
- Additional contextual data

### 3. **Admin Dashboard Integration**
- **Real-time Activity Monitoring**: View live user activities as they happen
- **Advanced Filtering**: Filter activities by type (page visits, clicks, form submissions)
- **Pagination**: Handle large datasets efficiently
- **Activity Statistics**: Comprehensive analytics and metrics
- **User Analytics**: Track unique users and activity patterns

## 📊 Database Schema

### UserActivity Model
```python
class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_identifier = db.Column(db.String(100), nullable=True)  # Anonymous user session ID
    action_type = db.Column(db.String(50), nullable=False)       # Type of action
    page = db.Column(db.String(200), nullable=False)            # Page where action occurred
    element_id = db.Column(db.String(100), nullable=True)       # Element that was interacted with
    user_agent = db.Column(db.String(500), nullable=True)       # Browser information
    ip_address = db.Column(db.String(45), nullable=True)        # User's IP address
    timestamp = db.Column(db.DateTime, default=datetime.utcnow) # When action occurred
    additional_data = db.Column(db.Text, nullable=True)         # Extra data as JSON
```

## 🔧 API Endpoints

### Tracking Endpoints

#### `POST /api/track`
Manual tracking endpoint for custom events.

**Request Body:**
```json
{
    "action_type": "button_click",
    "page": "/",
    "element_id": "submit-btn",
    "additional_data": "{\"element_text\": \"Submit Form\"}"
}
```

### Admin Endpoints

#### `GET /api/admin/activities`
Retrieve user activities with pagination and filtering.

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 50)
- `action_type`: Filter by action type
- `user_id`: Filter by user identifier

**Response:**
```json
{
    "activities": [...],
    "total": 150,
    "page": 1,
    "per_page": 20,
    "pages": 8
}
```

#### `GET /api/admin/activity-stats`
Get activity statistics and analytics.

**Response:**
```json
{
    "action_stats": {
        "page_visit": 45,
        "button_click": 23,
        "form_submit": 12
    },
    "unique_users": 8,
    "total_activities": 80,
    "recent_activities": 15
}
```

## 🎯 Action Types

The system tracks the following action types:

1. **`page_visit`** - User navigates to a page
2. **`button_click`** - User clicks a button or link
3. **`form_submit`** - User submits a form (attempt)
4. **`form_submit_success`** - Form submission successful
5. **`form_submit_error`** - Form submission failed
6. **`input_focus`** - User focuses on an input field

## 🔒 Privacy & Security

### User Privacy
- **Anonymous Tracking**: No personally identifiable information is stored
- **Session-Based**: Users are identified by anonymous session IDs
- **Temporary Data**: IP addresses are stored for security but can be anonymized

### Data Security
- **Admin Authentication**: All admin endpoints require authentication
- **Data Validation**: All tracking data is validated and sanitized
- **Error Handling**: Graceful error handling prevents tracking failures from breaking the app

## 📱 JavaScript Tracking Library

### Automatic Setup
The tracking library (`public/tracking.js`) is automatically included in all pages and provides:

- **Zero-configuration tracking** for common interactions
- **Debounced requests** to prevent spam
- **Retry logic** for failed requests
- **Debug mode** for development

### Manual Tracking
```javascript
// Track custom events manually
UserTracking.track('custom_action', 'element-id', {
    custom_data: 'value'
});

// Configure tracking settings
UserTracking.config({
    debug: true,
    trackPageViews: false
});
```

### Configuration Options
```javascript
const trackingConfig = {
    endpoint: '/api/track',
    trackPageViews: true,
    trackButtonClicks: true,
    trackFormSubmissions: true,
    trackInputFocus: true,
    debounceTime: 300,
    maxRetries: 3,
    debug: false
};
```

## 🚀 Usage Examples

### Viewing Activity Logs
1. Log in to the admin dashboard at `/admin/login`
2. Navigate to the "User Activities" tab
3. Use filters to view specific activity types
4. Use pagination to browse through historical data

### Monitoring Statistics
1. Go to the "Activity Statistics" tab in the admin dashboard
2. View overall metrics (total activities, unique users, recent activity)
3. See activity breakdown by type
4. Monitor user engagement patterns

### Custom Tracking
```javascript
// Track when users view specific content
UserTracking.track('content_view', 'article-123', {
    article_title: 'Sample Article',
    reading_time: '5 minutes'
});

// Track user preferences
UserTracking.track('preference_change', 'theme-toggle', {
    new_theme: 'dark',
    previous_theme: 'light'
});
```

## 🔍 Monitoring & Analytics

### Real-Time Monitoring
- Activities are logged in real-time as users interact with the site
- Admin dashboard auto-refreshes every 30 seconds
- Immediate feedback on user engagement

### Analytics Insights
- **User Behavior**: Understand how users navigate your site
- **Popular Actions**: See which buttons and forms are used most
- **Traffic Patterns**: Monitor page visit patterns
- **Error Tracking**: Identify form submission issues

### Performance
- **Minimal Overhead**: Tracking adds negligible performance impact
- **Asynchronous**: All tracking happens in the background
- **Fault Tolerant**: Tracking failures don't affect user experience

## 🛠️ Technical Implementation

### Flask Middleware
- **Request Middleware**: Automatically tracks page visits using `@app.before_request`
- **Form Enhancement**: Existing form routes enhanced with tracking
- **Error Handling**: Robust error handling prevents tracking from breaking the app

### Database Integration
- **SQLAlchemy Models**: Seamlessly integrated with existing database
- **Migration Ready**: New tables created automatically on app startup
- **Indexing**: Optimized for fast queries on timestamps and action types

### Frontend Integration
- **Vanilla JavaScript**: No dependencies, works with any frontend framework
- **Progressive Enhancement**: Site works perfectly even if tracking fails
- **Cross-Browser**: Compatible with all modern browsers

## 📋 Getting Started

### 1. Database Setup
The tracking tables are created automatically when you run the app:

```python
if __name__ == '__main__':
    init_database()  # Creates UserActivity table
    app.run()
```

### 2. Admin Access
Use the existing admin credentials:
- **Username**: `admin`
- **Password**: `password`

### 3. View Tracking Data
1. Start the application: `python app.py`
2. Visit any page to generate tracking data
3. Log in to admin dashboard
4. Navigate to "User Activities" tab

## 🎨 Customization

### Adding Custom Events
```python
# In your Flask routes
from app import log_user_activity

@app.route('/api/custom-action', methods=['POST'])
def custom_action():
    log_user_activity('custom_action', '/api/custom-action', 
                     element_id='custom-element',
                     additional_data='{"context": "custom"}')
    return jsonify({'success': True})
```

### Extending the JavaScript Library
```javascript
// Add custom tracking for specific elements
document.getElementById('special-button').addEventListener('click', function() {
    UserTracking.track('special_interaction', this.id, {
        timestamp: new Date().toISOString(),
        user_scroll_position: window.scrollY
    });
});
```

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Set debug mode for tracking
DEBUG=true

# Optional: Configure database
DATABASE_URL=sqlite:///tracking.db
```

### Tracking Settings
Modify the tracking configuration in `public/tracking.js`:
```javascript
UserTracking.config({
    debug: process.env.DEBUG === 'true',
    trackPageViews: true,
    debounceTime: 500  // Increase for high-traffic sites
});
```

This tracking system provides comprehensive insights into user behavior while maintaining privacy and security standards. It's designed to be lightweight, reliable, and easy to extend for your specific needs.
