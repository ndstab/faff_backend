# Task Management System

A Django-based task management system with WhatsApp integration, task completion notifications, and automated reminders.

## Features

- Create and assign tasks to multiple users
- Mark tasks as completed
- Receive notifications when all users complete a task
- Automated reminders at different intervals (24h, 6h, 2h, 1h before deadline)
- WhatsApp integration for task management

## Environment Setup

1. Clone the repository:
   ```
   git clone https://github.com/ndstab/faff_backend.git
   cd faff_backend
   ```

2. Create a virtual environment:
   ```
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file:
   ```
   cp env_example.txt .env
   ```

5. Edit the `.env` file with your specific settings:
   ```
   # Django settings
   SECRET_KEY=your-secret-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   # Database settings
   DATABASE_ENGINE=django.db.backends.sqlite3
   DATABASE_NAME=db.sqlite3

   # API URLs
   API_BASE_URL=http://localhost:8001
   WEBHOOK_URL=http://localhost:8001/webhooks/messages

   # Timezone settings
   TIME_ZONE=Asia/Kolkata
   ```

6. Run migrations:
   ```
   cd basiclogin
   python manage.py migrate
   ```

7. Start the development server:
   ```
   python manage.py runserver 0.0.0.0:8001
   ```

## Task Reminders

The system sends automated reminders at different intervals before task deadlines:
- 24 hours before deadline
- 6 hours before deadline
- 2 hours before deadline
- 1 hour before deadline

To set up automated reminders, a cron job is included:
```
# Run task reminders every hour
0 * * * * /path/to/faff_backend/run_task_reminders.sh
```

## API Endpoints

- `POST /api/register/` - Register a new user
- `GET /api/user-tasks/<phone_number>/` - Get tasks for a specific user
- `GET /api/users/` - Get all users
- `GET /api/tasks/` - Get all tasks
- `POST /api/tasks/<task_id>/complete/` - Mark a task as completed
- `POST /api/tasks/send-reminders/` - Manually send reminders

## WhatsApp Commands

- `TASK, [Person1|Person2], YYYY-MM-DD, Description` - Create a new task
- `LIST` - List all tasks
- `TASKS FOR Person` - List tasks for a specific person
- `DONE task-id` - Mark a task as completed
