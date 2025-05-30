# Smart Water Tanks - Deployment Guide

## Option 1: Railway (Recommended - Free & Easy)

Railway offers free hosting with PostgreSQL database and is very Django-friendly.

### Prerequisites
1. GitHub account
2. Railway account (sign up at https://railway.app)

### Step-by-Step Deployment

#### 1. Prepare Your Code
Your code is already prepared with the necessary files:
- `requirements.txt` - Python dependencies
- `Procfile` - Deployment commands
- `runtime.txt` - Python version
- `railway.json` - Railway configuration

#### 2. Push to GitHub
```bash
# Initialize git repository (if not already done)
git init
git add .
git commit -m "Initial commit - Smart Water Tanks Django App"

# Create a new repository on GitHub and push
git remote add origin https://github.com/yourusername/smart-water-tanks.git
git branch -M main
git push -u origin main
```

#### 3. Deploy on Railway

1. **Sign up/Login to Railway**
   - Go to https://railway.app
   - Sign up with your GitHub account

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `smart-water-tanks` repository

3. **Add PostgreSQL Database**
   - In your Railway project dashboard
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway will automatically create a PostgreSQL database

4. **Configure Environment Variables**
   - Go to your Django service in Railway
   - Click on "Variables" tab
   - Add these variables:
     ```
     SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
     DEBUG=False
     ALLOWED_HOSTS=yourdomain.railway.app
     ```
   - Railway automatically provides `DATABASE_URL` for PostgreSQL

5. **Deploy**
   - Railway will automatically deploy your app
   - The `release` command in Procfile will run migrations and populate sample data
   - Your app will be available at `https://yourdomain.railway.app`

#### 4. Access Your Application
- **URL**: Your Railway app URL (shown in dashboard)
- **Admin**: Create superuser by running in Railway console:
  ```bash
  python manage.py createsuperuser
  ```

### Railway Features
- ✅ **Free Tier**: $5/month credit (enough for small apps)
- ✅ **PostgreSQL Database**: Included
- ✅ **Automatic Deployments**: On git push
- ✅ **Custom Domains**: Available
- ✅ **SSL Certificates**: Automatic
- ✅ **Environment Variables**: Easy management

---

## Option 2: Heroku (Alternative)

### Prerequisites
- Heroku account
- Heroku CLI installed

### Steps
1. **Install Heroku CLI**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Or download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login and Create App**
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. **Add PostgreSQL**
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

4. **Set Environment Variables**
   ```bash
   heroku config:set SECRET_KEY="your-secret-key"
   heroku config:set DEBUG=False
   ```

5. **Deploy**
   ```bash
   git push heroku main
   ```

---

## Option 3: PythonAnywhere (Free Tier Available)

### Steps
1. Sign up at https://www.pythonanywhere.com
2. Upload your code via Files tab
3. Create a new web app (Django)
4. Configure WSGI file
5. Set up database (SQLite for free tier, PostgreSQL for paid)

---

## Post-Deployment Checklist

### 1. Create Superuser
```bash
# Railway: Use the console in Railway dashboard
# Heroku: heroku run python manage.py createsuperuser
python manage.py createsuperuser
```

### 2. Test Application
- [ ] Login page works
- [ ] Dashboard loads with charts
- [ ] Tank list displays
- [ ] Tank details show charts
- [ ] Alerts page works
- [ ] Data export functions
- [ ] Admin panel accessible

### 3. Sample Data
The deployment automatically runs:
```bash
python manage.py populate_sample_data
```

This creates:
- 5 sample water tanks across NYC boroughs
- 4 sensors per tank
- 30 days of hourly sensor data
- Sample alerts

### 4. Security Notes
- Change the SECRET_KEY in production
- Set DEBUG=False
- Configure proper ALLOWED_HOSTS
- Use environment variables for sensitive data

---

## Troubleshooting

### Common Issues

1. **Static Files Not Loading**
   - Ensure `whitenoise` is in requirements.txt
   - Check `STATICFILES_STORAGE` setting

2. **Database Connection Issues**
   - Verify `DATABASE_URL` environment variable
   - Check PostgreSQL service is running

3. **Migration Errors**
   - Run migrations manually: `python manage.py migrate`
   - Check database permissions

4. **Charts Not Displaying**
   - Verify Plotly.js is loading from CDN
   - Check browser console for JavaScript errors

### Getting Help
- Railway: https://docs.railway.app
- Django: https://docs.djangoproject.com
- Check application logs in Railway dashboard

---

## Cost Breakdown

### Railway (Recommended)
- **Free**: $5/month credit (sufficient for development)
- **Pro**: $20/month (for production apps)

### Heroku
- **Free tier discontinued**
- **Basic**: $7/month per dyno + database costs

### PythonAnywhere
- **Free**: Limited (good for testing)
- **Hacker**: $5/month (good for small apps)

**Recommendation**: Start with Railway's free tier for development and testing. 