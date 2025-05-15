import datetime
from django.utils import timezone
from .models import Task
from webhook.services import send_message


def send_task_reminders(hours_before=24):
    """
    Send reminders for tasks with upcoming deadlines.
    
    Args:
        hours_before (int): Send reminders for tasks due within this many hours
        
    Returns:
        tuple: (reminder_count, task_count) - Number of reminders sent and tasks processed
    """
    now = timezone.now()
    
    # Calculate the time range for reminders
    reminder_time = now + datetime.timedelta(hours=hours_before)
    
    print(f"Checking for tasks due by {reminder_time}")
    
    # For hour-specific reminders, we need to check the time as well
    # Convert to date for date-only fields, or keep datetime for datetime fields
    if hours_before <= 2:  # For short-term reminders (1-2 hours)
        # If Task.deadline includes time
        try:
            # Try to filter by datetime (if deadline is a datetime field)
            upcoming_tasks = Task.objects.filter(
                deadline__gte=now,
                deadline__lte=reminder_time,
                status='in_progress'
            )
        except Exception:
            # If deadline is a date-only field
            today = now.date()
            upcoming_tasks = Task.objects.filter(
                deadline=today,
                status='in_progress'
            )
    else:  # For longer-term reminders (24 hours, etc.)
        # If deadline is a date field
        reminder_date = reminder_time.date()
        upcoming_tasks = Task.objects.filter(
            deadline=reminder_date,
            status='in_progress'
        )
    
    reminder_count = 0
    
    for task in upcoming_tasks:
        print(f"Processing task: {task.id} - {task.description}")
        
        # Get all assigned users who haven't completed the task
        remaining_users = task.assigned_to.exclude(id__in=task.completed_by.all())
        
        # Prepare the reminder message
        reminder_message = f"⏰ Reminder: Task Due Soon ⏰\n"
        reminder_message += f"Description: {task.description}\n"
        reminder_message += f"Deadline: {task.deadline}\n"
        
        # Send reminder to the creator
        if task.created_by and task.created_by.phone_number:
            creator_message = reminder_message
            creator_message += f"\nThis is a reminder for a task you created."
            
            if remaining_users.exists():
                # List users who haven't completed the task
                names = [user.name for user in remaining_users]
                creator_message += f"\nStill waiting for: {', '.join(names)}"
            else:
                creator_message += "\nAll assigned users have completed this task."
            
            try:
                send_message(task.created_by.phone_number, creator_message)
                print(f"  Sent reminder to creator: {task.created_by.name}")
                reminder_count += 1
            except Exception as e:
                print(f"  Failed to send reminder to creator: {str(e)}")
        
        # Send reminders to assigned users who haven't completed the task
        for user in remaining_users:
            if user.phone_number:
                user_message = reminder_message
                user_message += f"\nYou have not yet completed this task."
                
                try:
                    send_message(user.phone_number, user_message)
                    print(f"  Sent reminder to assignee: {user.name}")
                    reminder_count += 1
                except Exception as e:
                    print(f"  Failed to send reminder to {user.name}: {str(e)}")
    
    return reminder_count, upcoming_tasks.count()
