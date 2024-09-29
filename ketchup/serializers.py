from django.contrib.auth.models import Group
from rest_framework import serializers, exceptions
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, KetchupEvent, Application, ApplicationStatus, Interest, AccountRoles, BusinessProfile, Message

class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'name']

class BusinessProfileSerializer(serializers.ModelSerializer):
    parser_classes = (FormParser, MultiPartParser)
    interests = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Interest.objects.all(),
        required=False
    )
    image = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    class Meta:
        model = BusinessProfile
        fields = '__all__'

    def to_internal_value(self, data):
        # `form-data` contains `interests`，convert to list
        interests = data.get('interests')
        print("data in to_internal_value", data)
        if interests:
            if isinstance(interests, str):
                # if `interests` is comma-sperated string, turn to list
                # print("enter isinstance(interests, str):",interests)
                # print("enter isinstance(interests, str) split:",interests.split(','))
                interests = [int(interest.strip()) for interest in interests.split(',')]
                # print("isinstance(interests, str):",interests)
            elif isinstance(interests, list):
                interests = [int(interest.id) if hasattr(interest, 'id') else int(interest) for interest in interests]
                print("isinstance(interests, list):",interests)
            else:
                raise serializers.ValidationError({
                    'interests': 'Interests must be a list of integers.'
                })
            data['interests'] = interests
        print("before return in to_internal_value: ", data)
        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        interests_data = validated_data.pop('interests', None)

        print('validated_data in BusinessprofileSerializer:', validated_data)
        print('interests_data in BusinessprofileSerializer:', interests_data)

        # update everything except 'interest'
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # update interest 'interests'
        if interests_data is not None:
            instance.interests.set(interests_data)
        print('instance in BusinessprofileSerializer:', instance.interests)
        return instance

class UserSerializer(serializers.HyperlinkedModelSerializer):
    interests = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Interest.objects.all(),
        required=False
    )
    business_profile = BusinessProfileSerializer(required=False)
    avatar_url = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'url', 'username', 'email', 'email_verified', 'firstname', 'lastname', 'interests','role', 'avatar', 'business_profile', 'privacy_level', 'avatar_url','bio', 'email_verified']

        extra_kwargs = {
            'privacy_level': {'required': False},
            'url': {'view_name': 'user_detail', 'lookup_field': 'id'}
        }
    
    def get_business_profile(self, obj):
        if obj.role == 'business' and hasattr(obj, 'business_profile'):
            business_profile = getattr(obj, 'business_profile', None)
            if business_profile:
                serializer = BusinessProfileSerializer(business_profile)
                return serializer.data
            return None
    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        else:
            return None
    def update(self, instance, validated_data):
        business_profile_data = validated_data.pop('business_profile', None)
        
        # user update
        instance = super().update(instance, validated_data)

        print("userserializer update begin business_profile_data:", business_profile_data)
        
        # BusinessProfile update
        if business_profile_data is not None:
            business_profile_instance = getattr(instance, 'business_profile', None)
            if business_profile_data is not None:
                request = self.context.get('request')
                if request and hasattr(request, 'FILES'):
                    print('business serializer: ' , request.FILES)
                    # extract file, assume field called 'image'
                    business_profile_image = request.FILES.get('image')
                    if business_profile_image:
                        business_profile_data['image'] = business_profile_image
                    business_profile_serializer = BusinessProfileSerializer(
                    business_profile_instance, 
                    data=business_profile_data, 
                    partial=True,
                    context={'request': request}
                )
                if business_profile_serializer.is_valid():
                    print("business_profile_serializer.is_valid() 1")
                    business_profile_serializer.save()
                else:
                    raise serializers.ValidationError(business_profile_serializer.errors)
        return instance



class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid username or password')

            if not user.check_password(password):
                raise exceptions.AuthenticationFailed('Invalid username or password')
            
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        response = {
            'username': str(username),
            'email': user.email,
            'refresh': str(refresh),
            'access': str(access_token),
            'role': user.role
        }

        # check if the username exsists in User or business
        if user.role == AccountRoles.USER:
            response['firstname'] = user.firstname
            response['lastname'] = user.lastname
        elif user.role == AccountRoles.BUSINESS:
            profile = user.business_profile
            response['name'] = profile.name
        else:
            raise exceptions.AuthenticationFailed('Role not specified')
        
        return response
    
class KetchupEventSerializer(serializers.ModelSerializer):
    applications = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)
    business_id = serializers.IntegerField(write_only=True, allow_null=True, required=False)
    business = UserSerializer(read_only=True)
    interests = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Interest.objects.all(), 
        required=False
    )
    interests_data = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Interest.objects.all(),
        source='interests',
        required=False
    )
    image = serializers.ImageField(required=False)

    def get_applications(self, obj):
        applications = Application.objects.filter(event=obj)
        return ApplicationSerializer(applications, many=True, context={'request': self.context['request']}).data

    class Meta:
        model = KetchupEvent
        fields = ['id','user', 'business', 'business_id', 'name', 'address', 'datetime', 'description', 'maxMemberCount', 'estimatedDuration', 'applications','interests', 'interests_data', 'image']
        read_only_fields = ['user']

    def create(self, validated_data):
        user = self.context['request'].user
        interests_data = validated_data.pop('interests', [])
        ketchup_event = KetchupEvent.objects.create(user=user, **validated_data)
        # for interest in interests_data:
        #     ketchup_event.interests.add(interest)
        ketchup_event.interests.set(interests_data)

        return ketchup_event
    
    def update(self, instance, validated_data):
        business_id = validated_data.pop('business_id', None)
        if business_id is not None:
            try:
                business = User.objects.get(id=business_id)
                instance.business = business
            except User.DoesNotExist:
                raise serializers.ValidationError({'business_id': 'No user found with the given ID.'})
        interests_data = validated_data.pop('interests', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if interests_data is not None:
            instance.interests.set(interests_data)

        instance.save()
        return instance
    
class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    class Meta:
        model = Message
        fields = ['sender', 'datetime', 'message', 'receiver']
    
class ApplicationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    event = serializers.PrimaryKeyRelatedField(queryset=KetchupEvent.objects.all())
    status = serializers.ReadOnlyField(default=ApplicationStatus.PENDING)

    class Meta:
        model = Application
        fields = ['id', 'user', 'event', 'status']
        read_only_fields = ['user']

    def validate_status(self, value):
        if value not in ApplicationStatus.values:
            raise serializers.ValidationError("Invalid status value. Must be 'pending', 'accepted' or 'rejected'.")
        return value