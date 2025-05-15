import json
import re
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from users.models import User
from .services import send_message, get_contact_numbers, TaskService, mark_task_as_done
from rest_framework.decorators import api_view
tasks_storage = TaskService()


def parse_task_completion(text):
    """
    Parse a task completion message to extract the task ID.
    
    Args:
        text (str): The message text, e.g., "DONE task-id-here"
        
    Returns:
        tuple: (task_id, error_message) - If successful, error_message will be None
    """
    parts = text.strip().split()
    if len(parts) < 2:
        return None, "Please provide a task ID. Format: DONE task-id"
    
    task_id = parts[1].strip()
    
    # Validate UUID format
    try:
        uuid_obj = uuid.UUID(task_id)
        return str(uuid_obj), None
    except ValueError:
        return None, f"Invalid task ID format: {task_id}. Please provide a valid task ID."


@csrf_exempt
@api_view(['POST'])
def whatsapp_webhook(request):
    try:
        if request.method != 'POST':
            return JsonResponse({"error": "Invalid request method"}, status=400)

        # Safely parse the request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in webhook request: {str(e)}")
            return JsonResponse({"status": "Invalid request format"}, status=200)  # Return 200 to acknowledge receipt
            
        # Safely extract message data with better error handling
        messages = data.get('messages', [])
        if not messages:
            print("No messages in webhook request")
            return JsonResponse({"status": "No messages found"}, status=200)  # Return 200 to acknowledge receipt
            
        message = messages[0]
        text = message.get('text', {}).get('body', '')
        from_number = message.get('from', '')

        if not text or not from_number:
            print(f"Missing required fields in webhook request: text={bool(text)}, from_number={bool(from_number)}")
            return JsonResponse({"status": "Missing required fields"}, status=200)  # Return 200 to acknowledge receipt

        received_text = text.strip()
        valid_commands = ['task', 'list', 'tasks for', 'done']
        is_valid_command = any(received_text.lower().startswith(cmd) for cmd in valid_commands)

        if received_text.lower().startswith('done'):
            # Handle task completion
            task_id, error = parse_task_completion(received_text)
            if error:
                send_message(from_number, error)
                return JsonResponse({"status": "Task completion error"}, status=200)
            
            # Attempt to mark task as done
            success, message = mark_task_as_done(task_id, from_number)
            
            # Send appropriate message back to the user
            send_message(from_number, message)
            
            return JsonResponse({"status": "Task completion processed", "success": success}, status=200)

        if not is_valid_command:
            # For unrecognized commands, just acknowledge receipt without error
            print(f"Received unrecognized message: {received_text[:50]}...")
            return JsonResponse({"status": "Message received (not a command)"}, status=200)

        print(f"Processing command: {received_text}")

        # TASK command
        if received_text.upper().startswith("TASK"):
            parts = [p.strip() for p in received_text.split(',')]
            people_input = parts[1] if len(parts) > 1 else ''
            people_match = re.match(r"\[(.*?)\]", people_input)

            if not people_input or not people_match:
                send_message(from_number, 'People must be enclosed in square brackets. Example: TASK, [John|Sarah], 2025-06-30, Project proposal')
                return JsonResponse({"status": "People input error"}, status=200)
            people = [p.strip() for p in people_match.group(1).split('|')]
            contact_numbers = get_contact_numbers(people)

            deadline = ''
            notes = ''
            if len(parts) >= 3:
                potential_deadline = parts[2]
                if re.match(r"\d{4}-\d{2}-\d{2}", potential_deadline):
                    deadline = potential_deadline
                    notes = ', '.join(parts[3:])
                else:
                    notes = ', '.join(parts[2:])

            # Get or create the user for the sender
            sender_user, _ = User.objects.get_or_create(phone_number=from_number)
            # Get assigned users
            assigned_users = [contact_numbers[p] for p in people]
            task = tasks_storage.add_task(notes, created_by_id=from_number, assigned_to_ids=assigned_users, deadline=deadline)
            task_message = f"New Task (ID: {task['id']}):\n"
            task_message += f"👥 People: {', '.join(people)}\n"
            if deadline:
                task_message += f"📅 Deadline: {deadline}\n"
            task_message += f"📝 Notes: {notes or 'No additional notes'}\n"
            task_message += "📱 Contact Numbers:\n" + '\n'.join([f"{name}: {number}" for name, number in contact_numbers.items()])

            send_message(from_number, task_message)

            for name, number in contact_numbers.items():
                if number != from_number:
                    try:
                        send_message(number, task_message)
                    except Exception as send_error:
                        print(f"Error sending message to {name} ({number}): {send_error}")

        # LIST command
        elif received_text.lower() == "list":
            tasks = tasks_storage.list_tasks()
            task_list_message = "\n\n".join([
                f"ID: {task.id}\n👥 People: {', '.join(task.people)}\n📅 Deadline: {task.deadline}\n📝 Notes: {task.notes or 'No notes'}\n🔖 Status: {task.status}"
                for task in tasks
            ]) or 'No tasks found.'
            send_message(from_number, f"Tasks:\n\n{task_list_message}")

        # TASKS FOR command
        elif received_text.lower().startswith("tasks for"):
            person_name = received_text.split('tasks for', 1)[1].strip()
            person_tasks = tasks_storage.get_tasks_for_person(person_name)
            task_list_message = "\n\n".join([
                f"ID: {task.id}\n👥 People: {', '.join(task.people)}\n📅 Deadline: {task.deadline}\n📝 Notes: {task.notes or 'No notes'}\n🔖 Status: {task.status}"
                for task in person_tasks
            ]) or f"No tasks found for {person_name}."
            send_message(from_number, f"Tasks for {person_name}:\n\n{task_list_message}")

        return JsonResponse({"status": "success"}, status=200)

    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        # Try to extract from_number if possible
        try:
            # Try to get the from_number from the request if it exists
            try:
                data = json.loads(request.body)
                messages = data.get('messages', [])
                if messages:
                    from_number = messages[0].get('from', '')
                else:
                    from_number = ''
            except Exception:
                from_number = ''
                
            # Only try to send a message if we have a valid number
            if from_number:
                send_message(from_number, 'Sorry, there was an error processing your request.')
        except Exception as send_error:
            print(f"Error sending error message: {str(send_error)}")
            
        # Always return a 200 status to acknowledge receipt
        return JsonResponse({"status": "Error processed", "error": str(e)}, status=200)
