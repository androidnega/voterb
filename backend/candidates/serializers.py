from rest_framework import serializers
from candidates.models import Candidate
from elections.models import Position, Department, Faculty
from elections.serializers import FacultySerializer, DepartmentSerializer


class PositionSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ['uuid', 'title']


class CandidateSerializer(serializers.ModelSerializer):
    position = PositionSimpleSerializer(read_only=True)
    position_uuid = serializers.UUIDField(write_only=True)
    faculty = FacultySerializer(read_only=True)
    academic_department = DepartmentSerializer(read_only=True)
    faculty_uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    department_uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Candidate
        fields = [
            'uuid', 'election', 'position', 'position_uuid', 'full_name',
            'faculty', 'academic_department', 'faculty_uuid', 'department_uuid',
            'department', 'photo', 'manifesto', 'status', 'ballot_number',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'election', 'created_at', 'updated_at']

    def _apply_academic_fields(self, validated_data):
        department_uuid = validated_data.pop('department_uuid', None)
        faculty_uuid = validated_data.pop('faculty_uuid', None)

        if department_uuid:
            department = Department.objects.select_related('faculty').filter(uuid=department_uuid).first()
            if not department:
                raise serializers.ValidationError({'department_uuid': 'Department not found'})
            validated_data['academic_department'] = department
            validated_data['faculty'] = department.faculty
            validated_data['department'] = department.name
        elif faculty_uuid:
            faculty = Faculty.objects.filter(uuid=faculty_uuid).first()
            if not faculty:
                raise serializers.ValidationError({'faculty_uuid': 'Faculty not found'})
            validated_data['faculty'] = faculty

        return validated_data

    def create(self, validated_data):
        position_uuid = validated_data.pop('position_uuid')
        position = Position.objects.get(uuid=position_uuid)
        validated_data['position'] = position
        validated_data = self._apply_academic_fields(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'position_uuid' in validated_data:
            position_uuid = validated_data.pop('position_uuid')
            validated_data['position'] = Position.objects.get(uuid=position_uuid)
        validated_data = self._apply_academic_fields(validated_data)
        return super().update(instance, validated_data)
