from django.utils import timezone
from rest_framework import serializers
from voting.models import Vote
from .models import (
    Election, Position, VoterEligibility, Faculty, Department, InstitutionCategory,
    VoterRegister, VoterCategory, VoterRegisterEntry,
)
from candidates.models import Candidate
from accounts.models import User
from elections.services.eligibility import apply_student_academic_placement, resolve_or_create_voter


class FacultyBriefSerializer(serializers.ModelSerializer):
    """Lightweight faculty payload for nesting under departments."""

    class Meta:
        model = Faculty
        fields = ['uuid', 'name', 'code']


class FacultySerializer(serializers.ModelSerializer):
    department_count = serializers.SerializerMethodField()

    class Meta:
        model = Faculty
        fields = ['uuid', 'name', 'code', 'description', 'is_active', 'department_count', 'created_at']
        read_only_fields = ['uuid', 'created_at']

    def get_department_count(self, obj):
        # Prefer annotated value from the list queryset when present.
        annotated = getattr(obj, 'active_department_count', None)
        if annotated is not None:
            return annotated
        return obj.departments.filter(is_active=True).count()


class FacultyWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = ['name', 'code', 'description', 'is_active']

    def validate_code(self, value):
        return value.strip().upper()


class DepartmentSerializer(serializers.ModelSerializer):
    faculty = FacultyBriefSerializer(read_only=True)
    faculty_uuid = serializers.UUIDField(write_only=True, required=False)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    faculty_code = serializers.CharField(source='faculty.code', read_only=True)

    class Meta:
        model = Department
        fields = [
            'uuid', 'name', 'code', 'description', 'is_active',
            'faculty', 'faculty_uuid', 'faculty_name', 'faculty_code', 'created_at',
        ]
        read_only_fields = ['uuid', 'created_at']

    def create(self, validated_data):
        faculty_uuid = validated_data.pop('faculty_uuid', None)
        if not faculty_uuid:
            raise serializers.ValidationError({'faculty_uuid': 'Select a faculty for this department.'})
        faculty = Faculty.objects.filter(uuid=faculty_uuid).first()
        if not faculty:
            raise serializers.ValidationError({'faculty_uuid': 'Faculty not found'})
        validated_data['faculty'] = faculty
        return super().create(validated_data)

    def update(self, instance, validated_data):
        faculty_uuid = validated_data.pop('faculty_uuid', None)
        if faculty_uuid:
            faculty = Faculty.objects.filter(uuid=faculty_uuid).first()
            if not faculty:
                raise serializers.ValidationError({'faculty_uuid': 'Faculty not found'})
            validated_data['faculty'] = faculty
        return super().update(instance, validated_data)

class DepartmentWriteSerializer(serializers.ModelSerializer):
    faculty_uuid = serializers.UUIDField()

    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'is_active', 'faculty_uuid']

    def validate_code(self, value):
        return value.strip().upper()

    def create(self, validated_data):
        faculty_uuid = validated_data.pop('faculty_uuid')
        faculty = Faculty.objects.filter(uuid=faculty_uuid).first()
        if not faculty:
            raise serializers.ValidationError({'faculty_uuid': 'Faculty not found'})
        validated_data['faculty'] = faculty
        return super().create(validated_data)

    def update(self, instance, validated_data):
        faculty_uuid = validated_data.pop('faculty_uuid', None)
        if faculty_uuid:
            faculty = Faculty.objects.filter(uuid=faculty_uuid).first()
            if not faculty:
                raise serializers.ValidationError({'faculty_uuid': 'Faculty not found'})
            validated_data['faculty'] = faculty
        return super().update(instance, validated_data)


class InstitutionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionCategory
        fields = ['uuid', 'name', 'code', 'description', 'is_active', 'created_at']
        read_only_fields = ['uuid', 'created_at']

    def validate_name(self, value):
        name = (value or '').strip()
        if not name:
            raise serializers.ValidationError('Category name is required.')
        return name

    def validate_code(self, value):
        return (value or '').strip().upper()


class ElectionRegisterSummarySerializer(serializers.ModelSerializer):
    """Small nested register payload used by election read APIs."""
    entry_count = serializers.SerializerMethodField()
    category_count = serializers.SerializerMethodField()

    class Meta:
        model = VoterRegister
        fields = ['uuid', 'name', 'description', 'entry_count', 'category_count']

    def get_entry_count(self, obj):
        from elections.services.register_service import register_voter_count
        return register_voter_count(obj)

    def get_category_count(self, obj):
        return obj.categories.count()


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ['uuid', 'full_name', 'photo', 'manifesto', 'status', 'ballot_number']
        read_only_fields = ['uuid']

class PositionSerializer(serializers.ModelSerializer):
    candidates = CandidateSerializer(many=True, read_only=True)
    restricted_categories = serializers.SerializerMethodField()
    restricted_category_uuids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Position
        fields = [
            'uuid', 'title', 'description', 'max_votes_allowed', 'display_order',
            'is_active', 'is_votable', 'allow_all_voters',
            'restricted_categories', 'restricted_category_uuids', 'candidates',
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']

    def get_restricted_categories(self, obj):
        return [
            {
                'uuid': str(c.uuid),
                'name': c.name,
                'register_uuid': str(c.register_id),
                'register_name': c.register.name if c.register_id else '',
            }
            for c in obj.restricted_categories.select_related('register').all()
        ]

    def validate(self, attrs):
        allow_all = attrs.get(
            'allow_all_voters',
            getattr(self.instance, 'allow_all_voters', True),
        )
        category_uuids = attrs.get('restricted_category_uuids', None)
        if category_uuids is None and self.instance is not None:
            has_categories = self.instance.restricted_categories.exists()
        else:
            has_categories = bool(category_uuids)

        if allow_all is False and not has_categories and self.partial is False:
            # On full create/update with allow_all=False, require at least one category
            if 'restricted_category_uuids' in attrs or self.instance is None:
                raise serializers.ValidationError({
                    'restricted_category_uuids': (
                        'Select at least one voter category when the position is restricted.'
                    )
                })
        return attrs

    def _set_categories(self, position, category_uuids):
        if category_uuids is None:
            return
        election = position.election
        categories = VoterCategory.objects.filter(
            uuid__in=category_uuids,
            register__election=election,
        )
        found = {str(c.uuid) for c in categories}
        missing = [str(u) for u in category_uuids if str(u) not in found]
        if missing:
            raise serializers.ValidationError({
                'restricted_category_uuids': (
                    'One or more categories do not belong to this election.'
                )
            })
        position.restricted_categories.set(categories)

    def create(self, validated_data):
        category_uuids = validated_data.pop('restricted_category_uuids', None)
        position = super().create(validated_data)
        if position.allow_all_voters:
            position.restricted_categories.clear()
        elif category_uuids is not None:
            self._set_categories(position, category_uuids)
        return position

    def update(self, instance, validated_data):
        category_uuids = validated_data.pop('restricted_category_uuids', None)
        position = super().update(instance, validated_data)
        if position.allow_all_voters:
            position.restricted_categories.clear()
        elif category_uuids is not None:
            self._set_categories(position, category_uuids)
        return position

class ElectionSerializer(serializers.ModelSerializer):
    positions = PositionSerializer(many=True, read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    register = ElectionRegisterSummarySerializer(read_only=True)
    eligible_voter_count = serializers.SerializerMethodField()
    votes_cast = serializers.SerializerMethodField()
    unique_voters = serializers.SerializerMethodField()
    can_manage = serializers.SerializerMethodField()
    owner_ec_unit_name = serializers.CharField(
        source='owner_ec_unit.name', read_only=True, default=None,
    )
    institution_name = serializers.CharField(
        source='institution.name', read_only=True, default=None,
    )

    class Meta:
        model = Election
        fields = [
            'uuid', 'title', 'description', 'status', 'start_date', 'end_date',
            'allow_web_voting', 'allow_ussd_voting', 'allow_sms_notifications',
            'register', 'created_by', 'positions', 'eligible_voter_count', 'votes_cast', 'unique_voters',
            'owner_type', 'institution_name', 'owner_ec_unit_name', 'can_manage',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'uuid', 'created_by', 'created_at', 'updated_at',
            'owner_type', 'can_manage',
        ]

    def get_eligible_voter_count(self, obj):
        from elections.services.register_service import election_register_user_count
        if obj.register_id or obj.registers.exists():
            return election_register_user_count(obj)
        return obj.eligibilities.filter(is_eligible=True).count()

    def to_representation(self, instance):
        from elections.services.register_service import ensure_election_uses_live_register

        # Legacy elections may still point at frozen clones — reattach to the live list.
        if ensure_election_uses_live_register(instance, sync=True):
            instance.refresh_from_db()
        return super().to_representation(instance)

    def get_votes_cast(self, obj):
        return Vote.objects.filter(election=obj).count()

    def get_unique_voters(self, obj):
        return Vote.objects.filter(election=obj).values('user').distinct().count()

    def get_can_manage(self, obj):
        request = self.context.get('request')
        if not request or not getattr(request, 'user', None):
            return False
        from elections.services.ec_access import user_can_manage_election
        return user_can_manage_election(request.user, obj)

class ElectionCreateUpdateSerializer(serializers.ModelSerializer):
    register = ElectionRegisterSummarySerializer(read_only=True)
    register_uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    clone_register = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = Election
        fields = [
            'uuid', 'title', 'description', 'status', 'start_date', 'end_date',
            'allow_web_voting', 'allow_ussd_voting', 'allow_sms_notifications',
            'register', 'register_uuid', 'clone_register',
        ]
        read_only_fields = ['uuid']

    def _clone_register_for_election(self, source_register, election):
        """
        Current register data is still stored under an election. When a new
        election is created from an existing register, copy the register,
        categories, and entries so the new election owns its voter list.
        """
        if not source_register or source_register.election_id == election.id:
            return source_register

        cloned_register = VoterRegister.objects.create(
            election=election,
            name=source_register.name,
            description=source_register.description,
            audience=getattr(source_register, 'audience', VoterRegister.AUDIENCE_SUB),
            institution=source_register.institution,
        )
        category_map = {}
        for category in source_register.categories.all():
            cloned_category = VoterCategory.objects.create(
                register=cloned_register,
                name=category.name,
                description=category.description,
                faculty=category.faculty,
                department=category.department,
            )
            category_map[category.pk] = cloned_category

        entries = []
        for entry in source_register.entries.all():
            entries.append(VoterRegisterEntry(
                register=cloned_register,
                category=category_map.get(entry.category_id),
                voter_id=entry.voter_id,
                full_name=entry.full_name,
                phone_number=entry.phone_number,
                gender=entry.gender,
                user=entry.user,
            ))
        if entries:
            VoterRegisterEntry.objects.bulk_create(entries)
        return cloned_register

    def _assign_register(self, election, selected_register, clone_register=False):
        from elections.services.register_service import sync_eligibility_from_registers

        # Institutional registers are always shared live lists (one register = one count).
        # Never snapshot/clone them — approved edits must flow into every linked election.
        if getattr(selected_register, 'institution_id', None):
            clone_register = False

        if clone_register:
            election.register = self._clone_register_for_election(selected_register, election)
        else:
            election.register = selected_register
        election.save(update_fields=['register', 'updated_at'])
        sync_eligibility_from_registers(election)
        return election

    def create(self, validated_data):
        selected_register = validated_data.pop('register', None)
        clone_register = validated_data.pop('clone_register', False)

        owner_fields = {
            k: validated_data.pop(k)
            for k in ('owner_type', 'institution', 'owner_ec_unit')
            if k in validated_data
        }
        if not owner_fields:
            request = self.context.get('request')
            user = getattr(request, 'user', None) if request else None
            if user:
                from elections.services.ec_access import resolve_create_owner
                owner_fields = resolve_create_owner(user)

        election = super().create({**validated_data, **owner_fields})
        if selected_register:
            self._assign_register(election, selected_register, clone_register=clone_register)
        return election

    def update(self, instance, validated_data):
        validated_data.pop('owner_type', None)
        validated_data.pop('institution', None)
        validated_data.pop('owner_ec_unit', None)
        selected_register = validated_data.pop('register', serializers.empty)
        clone_register = validated_data.pop('clone_register', False)
        election = super().update(instance, validated_data)
        if selected_register is not serializers.empty:
            if selected_register is None:
                election.register = None
                election.save(update_fields=['register', 'updated_at'])
            else:
                self._assign_register(election, selected_register, clone_register=clone_register)
        return election

    def validate(self, attrs):
        register_uuid = attrs.pop('register_uuid', serializers.empty)
        if register_uuid is not serializers.empty:
            if register_uuid is None:
                attrs['register'] = None
            else:
                register = VoterRegister.objects.filter(uuid=register_uuid).first()
                if not register:
                    raise serializers.ValidationError({'register_uuid': 'Voter register not found.'})
                attrs['register'] = register

        start = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end = attrs.get('end_date', getattr(self.instance, 'end_date', None))
        if start and end and end <= start:
            raise serializers.ValidationError({'end_date': 'End date must be after the start date.'})

        web = attrs.get('allow_web_voting', getattr(self.instance, 'allow_web_voting', True))
        ussd = attrs.get('allow_ussd_voting', getattr(self.instance, 'allow_ussd_voting', False))
        if self.instance is None or 'allow_web_voting' in attrs or 'allow_ussd_voting' in attrs:
            if not web and not ussd:
                raise serializers.ValidationError(
                    {'allow_web_voting': 'Enable Web Voting and/or USSD Voting.'}
                )

        # SMS channel is gated by the super-admin sms_notifications feature flag
        if attrs.get('allow_sms_notifications'):
            from system.models import FeatureFlag
            sms_flag = FeatureFlag.objects.filter(key='sms_notifications').first()
            if not sms_flag or not sms_flag.is_enabled:
                attrs['allow_sms_notifications'] = False

        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None
        selected_register = attrs.get('register', getattr(self.instance, 'register', None))

        if user and not self.instance:
            from elections.models import Election as ElectionModel
            from elections.services.ec_access import (
                ElectionAccessBlocked,
                register_matches_sub_ec_scope,
                resolve_create_owner,
            )
            try:
                owner = resolve_create_owner(user)
            except ElectionAccessBlocked as exc:
                raise serializers.ValidationError({'detail': str(exc)}) from exc

            if owner['owner_type'] == ElectionModel.OWNER_MAIN:
                if selected_register and hasattr(selected_register, 'is_approved') and not selected_register.is_approved:
                    raise serializers.ValidationError({
                        'register_uuid': 'Select an approved institutional voter register.',
                    })
                if selected_register and getattr(selected_register, 'audience', None) != ElectionModel.OWNER_MAIN:
                    # OWNER_MAIN value matches VoterRegister.AUDIENCE_MAIN ('main')
                    raise serializers.ValidationError({
                        'register_uuid': (
                            'Main EC elections must use a Main EC institution category register. '
                            'Faculty/department registers belong to Sub EC elections.'
                        ),
                    })
            elif owner['owner_type'] == ElectionModel.OWNER_SUB:
                if not selected_register:
                    raise serializers.ValidationError({
                        'register_uuid': 'Sub EC elections require a faculty/department register.',
                    })
                if getattr(selected_register, 'audience', None) == ElectionModel.OWNER_MAIN:
                    raise serializers.ValidationError({
                        'register_uuid': (
                            'This register is reserved for Main EC institution-wide elections. '
                            'Choose a faculty/department register in your Sub EC scope.'
                        ),
                    })
                if not register_matches_sub_ec_scope(selected_register, owner['owner_ec_unit']):
                    raise serializers.ValidationError({
                        'register_uuid': (
                            'This register is outside your Sub EC faculty/department scope. '
                            'Choose a register that matches your assigned categories.'
                        ),
                    })

        return attrs

class UserBasicSerializer(serializers.ModelSerializer):
    faculty = FacultySerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'uuid', 'email', 'index_number', 'first_name', 'last_name', 'phone_number',
            'faculty', 'department', 'programme', 'onboarding_completed',
        ]

class VoterEligibilitySerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    verified_by = UserBasicSerializer(read_only=True)
    user_uuid = serializers.UUIDField(write_only=True, required=False)
    user_identifier = serializers.CharField(write_only=True, required=False, allow_blank=True)
    faculty_uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    department_uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = VoterEligibility
        fields = [
            'uuid', 'election', 'user', 'user_uuid', 'user_identifier',
            'faculty_uuid', 'department_uuid',
            'is_eligible', 'verified_by', 'verified_at', 'created_at',
        ]
        read_only_fields = ['uuid', 'election', 'verified_by', 'verified_at', 'created_at']

    def validate(self, data):
        if not data.get('user_uuid') and not (data.get('user_identifier') or '').strip():
            raise serializers.ValidationError({
                'user_identifier': 'Enter a student index number.',
            })
        identifier = (data.get('user_identifier') or '').strip()
        if identifier and '@' in identifier:
            raise serializers.ValidationError({
                'user_identifier': 'Students are identified by index number only.',
            })
        if not data.get('faculty_uuid') or not data.get('department_uuid'):
            raise serializers.ValidationError({
                'faculty_uuid': 'Select faculty and department for this voter.',
            })
        return data

    def create(self, validated_data):
        user_uuid = validated_data.pop('user_uuid', None)
        user_identifier = validated_data.pop('user_identifier', None)
        faculty_uuid = validated_data.pop('faculty_uuid', None)
        department_uuid = validated_data.pop('department_uuid', None)
        election = validated_data.get('election')
        request = self.context.get('request')
        user = None
        error_message = None

        if user_uuid:
            user = User.objects.filter(uuid=user_uuid).first()
            if not user:
                error_message = 'Student not found.'
        elif user_identifier:
            user, error_message = resolve_or_create_voter(user_identifier)

        if error_message:
            raise serializers.ValidationError({'user_identifier': error_message})

        if not user:
            raise serializers.ValidationError({
                'user_identifier': 'Enter a student index number.',
            })

        try:
            apply_student_academic_placement(
                user,
                faculty_uuid=faculty_uuid,
                department_uuid=department_uuid,
            )
            user.save()
        except ValueError as exc:
            raise serializers.ValidationError({'faculty_uuid': str(exc)}) from exc

        if VoterEligibility.objects.filter(election=election, user=user).exists():
            label = user.index_number or user.uuid
            raise serializers.ValidationError({
                'user_identifier': f'{label} is already eligible for this election.',
            })

        validated_data['user'] = user
        validated_data['verified_by'] = request.user
        validated_data['verified_at'] = timezone.now()
        return super().create(validated_data)


# ─── VOTER REGISTER SERIALIZERS ────────────────────────────────

class VoterCategorySerializer(serializers.ModelSerializer):
    entry_count = serializers.SerializerMethodField()
    name = serializers.CharField(required=False, allow_blank=True, max_length=100)
    faculty_uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    department_uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True, default=None)
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)
    faculty = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    category_type = serializers.CharField(read_only=True)
    scope_label = serializers.CharField(read_only=True)

    class Meta:
        model = VoterCategory
        fields = [
            'uuid', 'name', 'description', 'entry_count', 'created_at',
            'faculty_uuid', 'department_uuid', 'faculty_name', 'department_name',
            'faculty', 'department',
            'category_type', 'scope_label',
        ]
        read_only_fields = ['uuid', 'created_at', 'category_type', 'scope_label']

    def get_entry_count(self, obj):
        return obj.entries.count()

    def get_faculty(self, obj):
        if not obj.faculty_id:
            return None
        return {'uuid': str(obj.faculty.uuid), 'name': obj.faculty.name, 'code': obj.faculty.code}

    def get_department(self, obj):
        if not obj.department_id:
            return None
        return {
            'uuid': str(obj.department.uuid),
            'name': obj.department.name,
            'code': obj.department.code,
            'faculty_uuid': str(obj.department.faculty_id) if obj.department.faculty_id else None,
        }

    def validate(self, attrs):
        faculty_uuid = attrs.get('faculty_uuid', serializers.empty)
        department_uuid = attrs.get('department_uuid', serializers.empty)
        # On create, at least one of faculty/department/name should identify the category.
        if not self.instance:
            has_faculty = faculty_uuid not in (None, serializers.empty, '')
            has_department = department_uuid not in (None, serializers.empty, '')
            has_name = bool((attrs.get('name') or '').strip())
            if has_faculty and has_department:
                raise serializers.ValidationError({
                    'faculty_uuid': 'Assign either a faculty or a department, not both.',
                })
            if not has_faculty and not has_department and not has_name:
                raise serializers.ValidationError({
                    'faculty_uuid': 'Select a faculty or department category.',
                })
        elif faculty_uuid not in (serializers.empty,) and department_uuid not in (serializers.empty,):
            if faculty_uuid and department_uuid:
                raise serializers.ValidationError({
                    'faculty_uuid': 'Assign either a faculty or a department, not both.',
                })
        return attrs

    def create(self, validated_data):
        faculty_uuid = validated_data.pop('faculty_uuid', None)
        department_uuid = validated_data.pop('department_uuid', None)
        faculty = None
        department = None
        if faculty_uuid:
            faculty = Faculty.objects.filter(uuid=faculty_uuid, is_active=True).first()
            if not faculty:
                raise serializers.ValidationError({'faculty_uuid': 'Faculty not found.'})
            validated_data['faculty'] = faculty
            validated_data['department'] = None
            validated_data.setdefault('name', faculty.name)
        elif department_uuid:
            department = Department.objects.filter(uuid=department_uuid, is_active=True).select_related('faculty').first()
            if not department:
                raise serializers.ValidationError({'department_uuid': 'Department not found.'})
            validated_data['department'] = department
            validated_data['faculty'] = None
            validated_data.setdefault('name', department.name)
        if not (validated_data.get('name') or '').strip():
            raise serializers.ValidationError({'name': 'Category name is required.'})
        return super().create(validated_data)

    def update(self, instance, validated_data):
        faculty_uuid = validated_data.pop('faculty_uuid', serializers.empty)
        department_uuid = validated_data.pop('department_uuid', serializers.empty)
        if faculty_uuid is not serializers.empty:
            if faculty_uuid:
                faculty = Faculty.objects.filter(uuid=faculty_uuid, is_active=True).first()
                if not faculty:
                    raise serializers.ValidationError({'faculty_uuid': 'Faculty not found.'})
                instance.faculty = faculty
                instance.department = None
                validated_data.setdefault('name', faculty.name)
            else:
                instance.faculty = None
        if department_uuid is not serializers.empty:
            if department_uuid:
                department = Department.objects.filter(uuid=department_uuid, is_active=True).first()
                if not department:
                    raise serializers.ValidationError({'department_uuid': 'Department not found.'})
                instance.department = department
                instance.faculty = None
                validated_data.setdefault('name', department.name)
            else:
                instance.department = None
        return super().update(instance, validated_data)


class VoterRegisterWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoterRegister
        fields = ['uuid', 'name', 'description']
        read_only_fields = ['uuid']


class VoterRegisterSerializer(serializers.ModelSerializer):
    categories = VoterCategorySerializer(many=True, read_only=True)
    entry_count = serializers.SerializerMethodField()
    category_count = serializers.SerializerMethodField()
    institution_uuid = serializers.UUIDField(source='institution.uuid', read_only=True, default=None)
    institution_name = serializers.CharField(source='institution.name', read_only=True, default=None)
    is_approved = serializers.BooleanField(read_only=True)
    pending_replace = serializers.SerializerMethodField()
    pending_entry_edits = serializers.SerializerMethodField()
    linked_election_count = serializers.SerializerMethodField()

    class Meta:
        model = VoterRegister
        fields = [
            'uuid', 'name', 'description', 'categories',
            'entry_count', 'category_count', 'created_at',
            'institution_uuid', 'institution_name', 'audience',
            'approval_status', 'approved_at', 'is_approved',
            'pending_replace', 'pending_entry_edits', 'linked_election_count',
        ]
        read_only_fields = ['uuid', 'created_at', 'approval_status', 'approved_at', 'audience']

    def get_entry_count(self, obj):
        from elections.services.register_service import register_voter_count
        return register_voter_count(obj)

    def get_category_count(self, obj):
        return obj.categories.count()

    def get_pending_replace(self, obj):
        staging = (
            obj.pending_replacements
            .filter(approval_status=VoterRegister.APPROVAL_PENDING)
            .order_by('-created_at')
            .first()
        )
        if not staging:
            return None
        from elections.services.register_service import register_voter_count
        return {
            'staging_uuid': str(staging.uuid),
            'entry_count': register_voter_count(staging),
            'created_at': staging.created_at.isoformat() if staging.created_at else None,
        }

    def get_pending_entry_edits(self, obj):
        """
        Proposed individual voter edits awaiting dual Main EC approval.
        Live register rows stay on pre-approval data until enrollment.
        """
        from accounts.models import MainECDecision

        decisions = (
            MainECDecision.objects.filter(
                status=MainECDecision.STATUS_PENDING,
                decision_type=MainECDecision.TYPE_REGISTER_ENTRY_UPDATE,
                payload__register_uuid=str(obj.uuid),
            )
            .order_by('-created_at')[:100]
        )
        out = []
        for decision in decisions:
            payload = decision.payload or {}
            out.append({
                'decision_uuid': str(decision.uuid),
                'entry_uuid': payload.get('entry_uuid'),
                'before': payload.get('before') or {},
                'proposed': {
                    'voter_id': payload.get('voter_id'),
                    'full_name': payload.get('full_name'),
                    'phone_number': payload.get('phone_number') or '',
                },
                'title': decision.title,
                'proposed_by': getattr(decision.proposed_by, 'email', '') or '',
                'created_at': decision.created_at.isoformat() if decision.created_at else None,
            })
        return out

    def get_linked_election_count(self, obj):
        from elections.models import Election
        return Election.objects.filter(register=obj).count()


class VoterRegisterEntrySerializer(serializers.ModelSerializer):
    category = VoterCategorySerializer(read_only=True)
    category_uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = VoterRegisterEntry
        fields = [
            'uuid', 'voter_id', 'full_name', 'phone_number', 'gender',
            'category', 'category_uuid', 'user', 'created_at',
        ]
        read_only_fields = ['uuid', 'created_at']
