from django.db import models
import uuid

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.name} ({self.phone_number})"

class Task(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ]

    description = models.TextField()
    
    # Relationships
    def get_default_user():
        try:
            return User.objects.first()
        except User.DoesNotExist:
            return None

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_by', default=get_default_user)
    assigned_to = models.ManyToManyField(User, related_name='assigned_to', blank=True)
    completed_by = models.ManyToManyField(User, related_name='completed_tasks', blank=True)
    
    # Task Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    deadline = models.DateField(null=True, blank=True)
    
    def is_completed_by_all(self):
        """Check if all assigned users have completed the task"""
        return self.assigned_to.count() > 0 and self.completed_by.count() == self.assigned_to.count()

    def __str__(self):
        return f"{self.description} (Status: {self.status})"
