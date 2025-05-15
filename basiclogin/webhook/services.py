import json
import os
import requests
from django.conf import settings
from users.models import User, Task
from datetime import datetime
from django.utils.dateparse import parse_date
import re
import uuid

def get_contact_numbers(names):
    """
    Get phone numbers for a list of names using the Django ORM.

    Args:
        names (list): List of names to look up.

    Returns:
        dict: Dictionary with names and their corresponding phone numbers.
    """
    contact_numbers = {}
    trimmed_names = [name.strip() for name in names]
    
    # Fetch matching users in a single query
    users = User.objects.filter(name__in=trimmed_names)

    # Create a mapping from name to phone_number
    for user in users:
        clean_number = user.phone_number.lstrip('+').strip()
        contact_numbers[user.name] = clean_number

    return contact_numbers


def send_message(to, message):
    url = "https://gate.whapi.cloud/messages/text"
    headers = {
        "Authorization": "Bearer ePaUEt9L8RzS9gPdKoyI6GVJkRb57bnB", #use your own whapi key here
        "Content-Type": "application/json"
    }
    payload = {
        "to": to,
        "body": message
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"Message sent to {to}")
        else:
            print(f"Failed to send message to {to}: {response.text}")
    except Exception as e:
        print(f"Error sending message to {to}: {e}")


from users.models import Task, User
from users.serializers import TaskSerializer

def mark_task_as_done(task_id, user_phone_number):
    """
    Mark a task as completed
    
    Args:
        task_id (str): UUID of the task to mark as done
        user_phone_number (str): Phone number of the user marking the task
    
    Returns:
        bool: True if task was successfully marked as done, False otherwise
    """
    try:
        # Find the task
        task = Task.objects.get(id=task_id)
        
        # Verify the user is assigned to the task
        user = User.objects.get(phone_number=user_phone_number)
        if user not in task.assigned_to.all():
            print(f"User {user_phone_number} is not assigned to this task")
            return False
        
        # Mark task as completed
        task.status = 'completed'
        task.save()
        
        print(f"Task {task_id} marked as completed by {user_phone_number}")
        return True
    
    except Task.DoesNotExist:
        print(f"Task {task_id} not found")
        return False
    except User.DoesNotExist:
        print(f"User {user_phone_number} not found")
        return False
from datetime import datetime
from django.utils.dateparse import parse_date

class TaskService:
    @staticmethod
    def add_task(description, created_by_id=None, assigned_to_ids=None, deadline=None):
        """
        Create and save a Task in the database.

        Args:
            description (str): Task description.
            created_by_id (str): Phone number of the User creating the task.
            assigned_to_ids (list): List of phone numbers to assign the task to.
            deadline (str or date): Optional deadline string (YYYY-MM-DD) or date.

        Returns:
            Task instance.
        """
        # Parse deadline string if needed
        if isinstance(deadline, str):
            deadline = parse_date(deadline)

        # Ensure created_by exists
        created_by, _ = User.objects.get_or_create(phone_number=created_by_id)
        # Create the task
        task = Task.objects.create(
            description=description,
            created_by=created_by,
            deadline=deadline
        )

        if assigned_to_ids:
            assigned_users = User.objects.filter(phone_number__in=assigned_to_ids)
            if not assigned_users.exists():
                assigned_users = [User.objects.get_or_create(phone_number=phone)[0] for phone in assigned_to_ids]
            task.assigned_to.set(assigned_users)
        
        # Serialize the task before returning
        serializer = TaskSerializer(task)
        return serializer.data


    @staticmethod
    def list_tasks():
        """
        Get all tasks.

        Returns:
            List of serialized tasks.
        """
        tasks = Task.objects.all()
        return TaskSerializer(tasks, many=True).data

    @staticmethod
    def get_tasks_for_person(user_id):
        """
        Get all tasks assigned to a specific user.

        Args:
            user_id (UUID): The user's ID.

        Returns:
            List of serialized tasks assigned to the user.
        """
        tasks = Task.objects.filter(assigned_to__id=user_id)
        return TaskSerializer(tasks, many=True).data


def mark_task_as_done(task_id, phone_number):
    """
    Mark a task as completed by a user.
    
    Args:
        task_id (str): The ID of the task to mark as done.
        phone_number (str): The phone number of the user marking the task as done.
        
    Returns:
        tuple: (success, message) - success is a boolean, message is a string with details
    """
    try:
        import requests
        import json
        from django.conf import settings
        
        # Clean the phone number
        clean_phone = phone_number.lstrip('+').strip()
        
        # Make a request to our own API
        api_base_url = os.environ.get('API_BASE_URL', 'http://localhost:8001')
        url = f"{api_base_url}/api/tasks/{task_id}/complete/"
        payload = {"phone_number": clean_phone}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        
        if response.status_code in [200, 201]:
            print(f"Task {task_id} marked as completed by {clean_phone}")
            
            # Check if task was deleted (all users completed)
            if response_data.get('status') == 'deleted':
                return True, "Task completed by all users and has been removed."
            else:
                # Task is still in progress, some users haven't completed yet
                completed_count = response_data.get('completed_count', 0)
                total_assigned = response_data.get('total_assigned', 0)
                
                message = f"You've marked this task as completed! ({completed_count}/{total_assigned} users completed)"
                
                # If there are remaining users, list them
                remaining_users = response_data.get('remaining_users', [])
                if remaining_users:
                    names = [user.get('name', 'Unknown') for user in remaining_users]
                    message += f"\nWaiting for: {', '.join(names)}"
                
                return True, message
        else:
            error_msg = response_data.get('error', 'Unknown error')
            print(f"Failed to mark task {task_id} as completed: {error_msg}")
            return False, f"Could not complete task: {error_msg}"
    except Exception as e:
        print(f"Error marking task as done: {e}")
        return False, f"Error: {str(e)}"
