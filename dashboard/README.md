# LLM Traceability Dashboard

A comprehensive, real-time dashboard for monitoring and analyzing your LiteLLM proxy usage with interactive charts and detailed session traceability.

## 🎯 Features

### 📊 **Real-time Analytics**
- **Overview Metrics**: Total requests, unique sessions, cost analysis, response times
- **Model Performance**: Usage distribution, cost breakdown, response time comparison
- **Token Analysis**: Prompt vs completion token usage by model
- **Cache Analytics**: Hit rates and performance optimization insights

### 🔍 **Session Traceability**
- **Advanced Search**: Filter by user, model, cost range, date range
- **Session Details**: Complete conversation history with message-level metrics
- **Interactive UI**: Click-through to detailed session analysis
- **Real-time Updates**: Auto-refresh every 30 seconds

### 📈 **Interactive Charts**
- **Model Usage**: Doughnut chart showing request distribution
- **Cost Analysis**: Bar chart of spending by model
- **Response Times**: Line chart comparing average and max response times
- **Token Distribution**: Stacked bar chart of prompt and completion tokens

### 🎨 **Modern UI/UX**
- **Bootstrap 5**: Responsive design for all devices
- **Chart.js**: Interactive, animated charts
- **FontAwesome**: Professional icons and indicators
- **Color-coded**: Status indicators and visual feedback
- **Loading States**: Professional loading animations

## 🚀 Quick Start

### 1. **Start the Dashboard Server**
```bash
cd dashboard
python serve.py
```

### 2. **Access the Dashboard**
Open your browser to: **http://localhost:3000**

### 3. **Ensure API is Running**
Make sure your traceability API is running at: **http://localhost:8000**

## 📱 Dashboard Sections

### 1. **Overview Metrics (Top Row)**
- **Total Requests**: Number of API calls in the last 7 days
- **Unique Sessions**: Count of distinct conversation sessions
- **Total Cost**: Dollar amount spent with token count
- **Avg Response Time**: Performance metric with cache hit rate

### 2. **Analytics Charts**
- **Model Usage Distribution**: Pie chart showing which models are used most
- **Cost Distribution**: Bar chart showing spending by model
- **Response Time Analysis**: Line chart comparing average vs maximum response times
- **Token Usage**: Stacked bars showing prompt and completion token distribution

### 3. **Session Search & Filtering**
- **Filter Options**:
  - User ID (dropdown with known users)
  - Model (dropdown with available models)
  - Cost range (min/max values)
  - Date range filtering
- **Search Results**:
  - Session cards with key metrics
  - Click-through to detailed session view
  - Cost visualization with progress bars

### 4. **Session Details Modal**
- **Session Overview**: User, agent, models used
- **Performance Metrics**: Total cost, tokens, duration
- **Message History**: Complete conversation trace
- **Per-Message Analytics**: Individual request metrics

### 5. **System Status**
- **API Health**: Real-time health check status
- **Database Connection**: Connection status monitoring
- **Last Updated**: Timestamp of latest data refresh

## 🔧 Configuration

### API Endpoint Configuration
Edit `script.js` to change the API URL:
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

### Auto-refresh Interval
Change the refresh interval (default: 30 seconds):
```javascript
setInterval(() => {
    refreshDashboard(false);
}, 30000); // 30 seconds
```

### Chart Colors
Customize chart colors in the chart creation functions:
```javascript
backgroundColor: [
    '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'
    // Add more colors as needed
],
```

## 📊 API Endpoints Used

The dashboard consumes all available traceability API endpoints:

### Analytics Endpoints
- `GET /api/v1/analytics/overview?days=7` - Overview metrics
- `GET /api/v1/analytics/models?days=7` - Model performance data

### Session Endpoints
- `POST /api/v1/sessions/search` - Session search with filters
- `GET /api/v1/sessions/{id}/summary` - Individual session summary
- `GET /api/v1/sessions/{id}/messages` - Session message history

### System Endpoints
- `GET /health` - API health status

## 🎨 Customization

### Adding New Metrics
1. **Add to Overview**: Modify `renderOverviewMetrics()` function
2. **Create New Chart**: Add chart creation function
3. **Update API Calls**: Add new endpoint calls in `loadModelAnalytics()`

### Custom Filters
1. **Add Form Elements**: Update filter section in `index.html`
2. **Update Search Logic**: Modify `searchSessions()` function
3. **Handle New Parameters**: Update filter object construction

### Styling Changes
1. **CSS Variables**: Modify colors and spacing in the `<style>` section
2. **Bootstrap Classes**: Update utility classes for different styling
3. **Chart Themes**: Customize Chart.js options for different appearance

## 🔍 Troubleshooting

### Dashboard Won't Load
1. **Check API Status**: Visit http://localhost:8000/health
2. **CORS Issues**: Ensure traceability API has CORS enabled
3. **Network Connectivity**: Check browser developer console for errors

### Charts Not Displaying
1. **API Response Format**: Verify API returns expected data structure
2. **Chart.js Loading**: Check if Chart.js library loaded successfully
3. **Console Errors**: Check browser console for JavaScript errors

### No Data Showing
1. **API Data**: Verify traceability API has data to return
2. **Time Range**: Try different day ranges (1, 7, 30 days)
3. **Database Connection**: Check if PostgreSQL database is accessible

### Search Not Working
1. **Filter Values**: Ensure filter values match database values
2. **Date Format**: Use ISO 8601 format for date ranges
3. **API Errors**: Check network tab for failed API calls

## 📚 Dependencies

### Frontend Libraries (CDN)
- **Bootstrap 5.3.0**: UI framework and responsive design
- **Chart.js**: Interactive charting library
- **FontAwesome 6.0.0**: Professional icon library
- **Chart.js Date Adapter**: Date handling for time-series charts

### Backend Requirements
- **Python 3.8+**: For the dashboard server
- **LiteLLM Proxy**: Running at localhost:4000
- **Traceability API**: Running at localhost:8000

## 🚀 Production Deployment

### For Production Use
1. **Use proper web server**: Nginx, Apache, or cloud hosting
2. **HTTPS**: Enable SSL/TLS for security
3. **Environment Variables**: Configure API endpoints via environment
4. **Authentication**: Add user authentication if needed
5. **Rate Limiting**: Implement rate limiting for API calls

### Docker Deployment
Create a simple Docker setup:
```dockerfile
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
COPY script.js /usr/share/nginx/html/
COPY README.md /usr/share/nginx/html/
EXPOSE 80
```

## 🎯 Demo Use Cases

### 1. **Cost Optimization**
- Monitor spending by model
- Identify high-cost sessions
- Track token usage patterns
- Optimize model selection

### 2. **Performance Analysis**
- Compare response times across models
- Monitor cache hit rates
- Track user session patterns
- Identify bottlenecks

### 3. **Usage Monitoring**
- Track daily/weekly usage trends
- Monitor user activity patterns
- Analyze conversation lengths
- Plan capacity requirements

### 4. **Troubleshooting**
- Search for specific user sessions
- Analyze failed requests
- Monitor system health
- Debug performance issues

This dashboard provides a complete view of your LLM proxy usage with all the metrics needed for monitoring, optimization, and troubleshooting! 🎉