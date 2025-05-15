from rest_framework import serializers
from .models import User, Task

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'phone_number']

class TaskSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(many=True, read_only=True)
    created_by_phone = serializers.CharField(write_only=True)
    assigned_to_phones = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)

    def create(self, validated_data):
        created_by_phone = validated_data.pop('created_by_phone')
        assigned_to_phones = validated_data.pop('assigned_to_phones', [])

        # Find the user who created the task
        created_by = User.objects.get(phone_number=created_by_phone)
        
        # Create the task
        task = Task.objects.create(created_by=created_by, **validated_data)

        # Add assigned users
        if assigned_to_phones:
            assigned_users = User.objects.filter(phone_number__in=assigned_to_phones)
            task.assigned_to.set(assigned_users)

        return task

    class Meta:
        model = Task
        fields = [
            'id', 'description', 'created_by', 'created_by_phone', 
            'assigned_to', 'assigned_to_phones', 'completed_by', 'status', 'deadline'
        ]

class WhatsAppTaskInputSerializer(serializers.Serializer):
    message = serializers.CharField()
