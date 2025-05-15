# Deploying to Render.com

Since Heroku requires payment verification, we can use Render.com which offers a generous free tier without requiring payment information upfront.

## Deployment Steps

1. **Sign up for Render**
   - Go to [render.com](https://render.com/) and sign up for a free account

2. **Create a new Web Service**
   - Click "New +" and select "Web Service"
   - Connect your GitHub repository or use the public repository URL
   - Select the repository with your Django application

3. **Configure the Web Service**
   - Name: `faff-backend`
   - Environment: `Python 3`
   - Build Command: `./build.sh`
   - Start Command: `cd basiclogin && gunicorn basiclogin.wsgi:application`
   - Select the free plan

4. **Add Environment Variables**
   - SECRET_KEY: (Generate a secure key)
   - DEBUG: False
   - ALLOWED_HOSTS: .onrender.com
   - TIME_ZONE: Asia/Kolkata
   - API_BASE_URL: (Your Render app URL, e.g., https://faff-backend.onrender.com)
   - WEBHOOK_URL: (Your Render app URL + /webhooks/messages)

5. **Create a PostgreSQL Database**
   - Click "New +" and select "PostgreSQL"
   - Name: `faff-db`
   - Select the free plan
   - After creation, copy the "Internal Database URL"

6. **Link Database to Web Service**
   - Go back to your web service settings
   - Add environment variable:
     - DATABASE_URL: (Paste the Internal Database URL)

7. **Deploy**
   - Click "Create Web Service"
   - Wait for the deployment to complete

## Setting Up Task Reminders

For task reminders, you can use Render's Cron Jobs:

1. **Create a new Cron Job**
   - Click "New +" and select "Cron Job"
   - Name: `faff-reminders-hourly`
   - Schedule: `0 * * * *` (every hour)
   - Command: `cd basiclogin && python manage.py send_task_reminders --hours=1 && python manage.py send_task_reminders --hours=2 && python manage.py send_task_reminders --hours=6`

2. **Create another Cron Job for daily reminders**
   - Name: `faff-reminders-daily`
   - Schedule: `0 0 * * *` (every day at midnight)
   - Command: `cd basiclogin && python manage.py send_task_reminders --hours=24`

## Update WhatsApp Integration

Update your WhatsApp Business API webhook URL to point to your Render app:
```
https://faff-backend.onrender.com/webhooks/messages
```
