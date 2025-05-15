from django.core.management.base import BaseCommand
from users.utils import send_task_reminders


class Command(BaseCommand):
    help = 'Send reminders for tasks with upcoming deadlines'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Send reminders for tasks due within this many hours'
        )

    def handle(self, *args, **options):
        hours_before = options['hours']
        
        self.stdout.write(f"Sending reminders for tasks due within {hours_before} hours")
        
        # Use the utility function to send reminders
        reminder_count, task_count = send_task_reminders(hours_before=hours_before)
        
        self.stdout.write(self.style.SUCCESS(f"Successfully sent {reminder_count} reminders for {task_count} tasks"))
