from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import User, Task
from .serializers import UserSerializer, TaskSerializer

@api_view(['POST'])
def register_user(request):
    """Register a new user or return existing user if phone number and name match"""
    print("Registration request:", request.data)
    serializer = UserSerializer(data=request.data)
    
    if serializer.is_valid():
        # Check if a user with the same phone number already exists
        existing_user = User.objects.filter(phone_number=serializer.validated_data['phone_number']).first()
        
        if existing_user:
            # If user exists, check if name matches
            if existing_user.name == serializer.validated_data['name']:
                # User exists with same name and phone number, return existing user data
                existing_serializer = UserSerializer(existing_user)
                return Response({
                    "message": "User already exists",
                    "user": existing_serializer.data
                }, status=status.HTTP_200_OK)
            else:
                # User exists with different name
                return Response(
                    {"error": "User with this phone number already exists with a different name"}, 
                    status=status.HTTP_409_CONFLICT
                )
        
        # Create new user if no existing user found
        new_user = serializer.save()
        return Response({
            "message": "User registered successfully",
            "user": serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_user(request):
    """Login a user by phone number and name"""
    print("Login request:", request.data)
    phone_number = request.data.get('phone_number')
    name = request.data.get('name')
    
    if not phone_number or not name:
        return Response({
            "error": "Phone number and name are required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(phone_number=phone_number, name=name)
        serializer = UserSerializer(user)
        return Response({
            "message": "Login successful",
            "user": serializer.data
        }, status=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        return Response({
            "error": "Invalid login credentials"
        }, status=status.HTTP_401_UNAUTHORIZED)
    except User.MultipleObjectsReturned:
        return Response({
            "error": "Multiple users found. Contact support."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_user_tasks(request, phone_number):
    try:
        user = User.objects.get(phone_number=phone_number)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Get tasks assigned to the user
    assigned_tasks = Task.objects.filter(assigned_to=user)

    # Serialize tasks
    assigned_tasks_serializer = TaskSerializer(assigned_tasks, many=True)

    return Response(assigned_tasks_serializer.data)

@api_view(['GET'])
def get_all_users(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_all_tasks(request):
    """Get all tasks in the system"""
    tasks = Task.objects.all()
    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def send_reminders(request):
    """Manually trigger task reminders"""
    from .utils import send_task_reminders
    
    # Get hours parameter from request, default to 24
    hours = request.data.get('hours', 24)
    try:
        hours = int(hours)
    except (ValueError, TypeError):
        return Response({"error": "Hours must be a valid integer"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Send reminders
    reminder_count, task_count = send_task_reminders(hours_before=hours)
    
    return Response({
        "message": f"Successfully sent {reminder_count} reminders for {task_count} tasks",
        "reminder_count": reminder_count,
        "task_count": task_count
    })

@api_view(['POST'])
def complete_task(request, task_id):
    """Mark a task as completed by a user and delete if all users have completed"""
    # Print request data for debugging
    print(f"Request data: {request.data}")
    print(f"Request content type: {request.content_type}")
    print(f"Task ID: {task_id}")
    
    try:
        # Get the task
        task = Task.objects.get(id=task_id)
        
        # Get the user from phone number
        phone_number = request.data.get('phone_number')
        print(f"Phone number from request: {phone_number}")
        
        if not phone_number:
            return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"Looking up user with phone number: {phone_number}")
        
        try:
            user = User.objects.get(phone_number=phone_number)
            print(f"Found user: {user.name} ({user.phone_number})")
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is assigned to this task
        if user not in task.assigned_to.all():
            print(f"User {user.name} is not assigned to task {task_id}")
            return Response({"error": "User is not assigned to this task"}, status=status.HTTP_403_FORBIDDEN)
        
        print(f"User {user.name} is assigned to task {task_id}")
        
        # Add user to completed_by if not already there
        if user not in task.completed_by.all():
            task.completed_by.add(user)
            print(f"Added user {user.name} to completed_by")
        else:
            print(f"User {user.name} already marked task as completed")
            
        # Check if all users have completed
        if task.is_completed_by_all():
            print(f"All users have completed task {task_id}. Sending notifications and deleting task.")
            
            # Get all users involved in the task
            all_users = list(task.assigned_to.all())
            creator = task.created_by
            
            # Add creator to notification list if not already in assigned users
            if creator not in all_users:
                all_users.append(creator)
            
            # Import the message sending function
            from webhook.services import send_message
            
            # Prepare completion message
            completion_message = f"🎉 Task Completed! 🎉\n"
            completion_message += f"Description: {task.description}\n"
            completion_message += f"All assigned users have completed this task.\n"
            completion_message += f"The task has been removed from the system.\n"
            completion_message += f"Thank you for your collaboration!"
            
            # Send message to all users
            for user in all_users:
                try:
                    if user.phone_number:
                        send_message(user.phone_number, completion_message)
                        print(f"Sent completion notification to {user.name} ({user.phone_number})")
                except Exception as e:
                    print(f"Failed to send notification to {user.name}: {str(e)}")
            
            # Delete the task
            task.delete()
            
            return Response({
                "message": "Task completed by all users and deleted",
                "status": "deleted",
                "notifications_sent": len(all_users)
            })
        else:
            # Return remaining users who haven't completed
            remaining_users = task.assigned_to.exclude(id__in=task.completed_by.all())
            remaining_serializer = UserSerializer(remaining_users, many=True)
            print(f"Task {task_id} completion recorded. {task.completed_by.count()}/{task.assigned_to.count()} users completed.")
            return Response({
                "message": "Task completion recorded",
                "status": "in_progress",
                "completed_count": task.completed_by.count(),
                "total_assigned": task.assigned_to.count(),
                "remaining_users": remaining_serializer.data
            })
            
    except Task.DoesNotExist:
        print(f"Task {task_id} not found")
        return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error in complete_task: {str(e)}")
        return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)