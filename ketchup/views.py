from django.contrib.auth.models import Group
from .models import User, KetchupEvent, Application, ApplicationStatus, Interest, AccountRoles, BusinessProfile, Message
from rest_framework import viewsets, permissions, status
from rest_framework.permissions import IsAuthenticated, BasePermission
from .serializers import UserSerializer, GroupSerializer, CustomTokenObtainPairSerializer,  KetchupEventSerializer, ApplicationSerializer, InterestSerializer, MessageSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_202_ACCEPTED, HTTP_200_OK
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from django.db import transaction
import yagmail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str, force_bytes
from django.urls import reverse
from django.shortcuts import redirect
from .tokens import account_activation_token
from django.db.models import Q
import os

def send_email(recipient_list, subject, message):
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
    with yagmail.SMTP(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD) as yag:
        yag.send(recipient_list, subject, message)
        print('email sent')

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserRegisterView(APIView):
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            username = request.data.get('username')
            password = request.data.get('password')
            email = request.data.get('email')
            role = request.data.get('role')
            firstname = request.data.get('firstname')
            lastname = request.data.get('lastname')
            # Check if username already exists
            if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
                return Response( {"message": "Username or email already exists. Please choose a different username."}, status=status.HTTP_409_CONFLICT)
            subject = "Verify your email"
            if role  == AccountRoles.USER:
                user = User.objects.create_user(username=username, password=password, email=email, firstname=firstname, lastname=lastname, role=role)
                token = account_activation_token.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                activation_link = request.build_absolute_uri(
                    reverse('activate_account', kwargs={'uidb64': uid, 'token': token})
                )
                message = f"Dear {firstname},\n\nYour new user account on Ketchup with username {username} is created. Please click on the link to verify your email and activate your account: {activation_link}, let's ketchup!"
                recipient_list = [email]
                send_email( recipient_list, subject, message )
                return Response({"message": "User registered successfully, please check your email for activation link."}, status=status.HTTP_201_CREATED)
            elif role == AccountRoles.BUSINESS:
                name = request.data.get('name')
                description = request.data.get('description')
                # create new user here
                user = User.objects.create_user(username=username, password=password, email=email, role=role)
                BusinessProfile.objects.create(user=user, name=name, description=description)
                token = account_activation_token.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                activation_link = request.build_absolute_uri(
                    reverse('activate_account', kwargs={'uidb64': uid, 'token': token})
                )
                message = f"Dear {name},\n\nYour new business account on Ketchup with username {username} is created. Please click on the link to verify your email and activate your account: {activation_link}, let's ketchup!"
                recipient_list = [email]
                send_email( recipient_list, subject, message )

                return Response({"message": "Business registered successfully."}, status=status.HTTP_201_CREATED)
            else:
                return Response({"message": "Invalid role specified."}, status=status.HTTP_400_BAD_REQUEST)

class ActivateAccount(APIView):
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.email_verified = True
            user.save()
            # Redirect to login page or success page after activation
            return redirect('https://ketchup-front.netlify.app/login')
        else:
            # Invalid link
            return Response({"message": "Activation link is invalid!"}, status=status.HTTP_400_BAD_REQUEST)
class IsOwnerOrEventOrganizerOrOpenToGroupOrPublic(BasePermission):
    """
    allow organizer/other users to retreive profile based on the profile privacy level
    """
    
    def has_object_permission(self, request, view, obj):
        if obj.privacy_level == 'public':
            return True

        if obj.privacy_level == 'openToGroup':
            if request.user.is_authenticated:
                # TODO: allow other members to view profile
                # return user_in_same_ketchup_event(request.user, obj)
                pass
            else:
                return False

        if obj.privacy_level == 'private':
            # TODO: only allow view profile from the user itself and the organizer of ketchup it's applying
            # if request.user.is_authenticated and (obj == request.user or is_event_organizer(request.user, obj)):
            #     return True
            #     pass
            # else:
            #     return False
            pass

        return False

class UserDetailView(APIView):
    def get_object(self, id):
        try:
            return User.objects.get(id=id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=HTTP_404_NOT_FOUND)

    def get(self, request, id, format=None):
        user = self.get_object(id)
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)
    
class BusinessUserDetailView(APIView):
    """
    Retrieve a user with a 'business' role by ID.
    """
    def get(self, request, id, format=None):
        try:
            business_user = User.objects.get(id=id, role='business')
        except User.DoesNotExist:
            return Response({"error": "Business user not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(business_user, context={'request': request})
        return Response(serializer.data)
    
class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get_object(self, id):
        try:
            return User.objects.get(id=id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=HTTP_404_NOT_FOUND)
    def get(self, request, id=None, format=None):
        if not IsAuthenticated().has_permission(request, self):
            return Response({"detail": "Authentication credentials were not provided."}, context={'request': request}, status=HTTP_403_FORBIDDEN)
        print('in ProfileView: ',request.user.id)
        if id is None:
            user = self.get_object(request.user.id)
        else:
            user = self.get_object(id)
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)
    
    def patch(self, request):
        print("patch begin request:", request)
        if not IsAuthenticated().has_permission(request, self):
            return Response({"detail": "Authentication credentials were not provided."}, context={'request': request}, status=HTTP_403_FORBIDDEN)
        user = self.get_object(request.user.id)
        if request.user != user:
            return Response({"detail": "You do not have permission to edit this user."}, status=status.HTTP_403_FORBIDDEN)
        serializer = UserSerializer(user, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            print("serializer.is_valid() 1:")
            serializer.save()
            return Response(serializer.data)
        print("serializer.is_valid() false:", serializer)
        print("serializer.errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class KetchEventListCreateAPIView(APIView):
    def get(self, request):
        ketch_events = KetchupEvent.objects.all().order_by('-id')
        interests = request.query_params.getlist('interests')
        for interest in interests:
            ketch_events = ketch_events.filter(interests=interest).distinct()
        serializer = KetchupEventSerializer(ketch_events,  context={'request': request}, many=True)
        return Response(serializer.data)

    def post(self, request):
        #TODO: check the role
        print('IsAuthenticated: ',IsAuthenticated())
        if not IsAuthenticated().has_permission(request, self):
            return Response({"detail": "Authentication credentials were not provided."}, context={'request': request}, status=HTTP_403_FORBIDDEN)
        serializer = KetchupEventSerializer(data=request.data)
        serializer.context['request'] = request
        if serializer.is_valid():
            datetime_str  = request.data.get('datetime')
            if datetime_str:
                datetime_obj = parse_datetime(datetime_str)
                business_id = request.data.get('business')
                # interests = request.data.get('interests')
                # print(interests)
                if business_id:
                    try:
                        # Assuming BusinessProfile is the related model for business
                        business = User.objects.get(id=business_id)
                        if business.role == AccountRoles.BUSINESS:
                            serializer.save(datetime=datetime_obj, business=business)
                        else:
                            return Response({"detail": "Invalid business ID provided"}, status=HTTP_400_BAD_REQUEST)
                        # ... (remaining part of the existing code)
                    except BusinessProfile.DoesNotExist:
                        return Response({"detail": "Invalid business ID provided"}, status=HTTP_400_BAD_REQUEST)
                if datetime_obj is not None:
                    if not timezone.is_aware(datetime_obj):
                        datetime_obj = timezone.make_aware(datetime_obj)
                    serializer.save(datetime=datetime_obj)
                    return Response(serializer.data, status=HTTP_201_CREATED)
                else:
                    return Response({"detail": "Invalid datetime for ketchupevent"}, context={'request': request}, status=HTTP_400_BAD_REQUEST)
            else:
                serializer.save()
                return Response(serializer.data, status=HTTP_201_CREATED)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

class KetchEventRetrieveAPIView(APIView):
    def get(self, request, id):
        try:
            ketch_event = KetchupEvent.objects.get(id=id)
            serializer = KetchupEventSerializer(ketch_event, context={'request': request})
            response_data = serializer.data.copy()
            if not isinstance(request.user, AnonymousUser):
                is_organizer = request.user == ketch_event.user
                is_accepted_member = ketch_event.applications.filter(
                    user=request.user, status="accepted"
                ).exists()
                try:
                    application = ketch_event.applications.get(user=request.user)
                    user_application_status = application.status
                except ketch_event.applications.model.DoesNotExist:
                    user_application_status = None
            else:
                # User is not authenticated
                is_organizer = False
                is_accepted_member = False
                user_application_status = None
            if not (is_organizer or is_accepted_member):
                response_data['applications'] = []
            response_data['is_organizer'] = is_organizer
            response_data['user_application_status'] = user_application_status
            return Response(response_data)
        except KetchupEvent.DoesNotExist:
            return Response({"error": "KetchEvent not found."}, status=HTTP_404_NOT_FOUND)
    def put(self, request, id):
        if not permissions.IsAuthenticated().has_permission(request, self):
            return Response({"detail": "Authentication credentials were not provided."}, status=HTTP_403_FORBIDDEN)
        try:
            ketch_event = KetchupEvent.objects.get(id=id)
            if request.user != ketch_event.user:
                return Response({"error": "You are not authorized to update this KetchupEvent."}, status=HTTP_403_FORBIDDEN)
            serializer = KetchupEventSerializer(ketch_event, data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        except KetchupEvent.DoesNotExist:
            return Response({"error": "KetchEvent not found."}, status=HTTP_404_NOT_FOUND)
    def delete(self, request, id):
        if not permissions.IsAuthenticated().has_permission(request, self):
            return Response({"detail": "Authentication credentials were not provided."}, status=403)
        try:
            ketch_event = KetchupEvent.objects.get(id=id)
            if request.user != ketch_event.user:
                return Response({"error": "You are not authorized to delete this KetchupEvent."}, status=HTTP_403_FORBIDDEN)
            ketch_event.delete()
            return Response({"success": "KetchEvent successfully deleted."}, status=HTTP_204_NO_CONTENT)
        except KetchupEvent.DoesNotExist:
            return Response({"error": "KetchEvent not found."}, status=HTTP_404_NOT_FOUND)
    
    def patch(self, request, id):
        try:
            ketch_event = KetchupEvent.objects.get(id=id)
        except KetchupEvent.DoesNotExist:
            return Response({"error": "KetchEvent not found."}, status=status.HTTP_404_NOT_FOUND)
        if request.user != ketch_event.user:
            return Response({"error": "You are not authorized to update this KetchEvent."}, status=status.HTTP_403_FORBIDDEN)

        serializer = KetchupEventSerializer(ketch_event, data=request.data, context={'request': request}, partial=True)
        
        if 'image' in request.data:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "No image provided."}, status=status.HTTP_400_BAD_REQUEST)

# TODO: application create, modify(change status) and get (the whole list based on event)
class ApplicationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not IsAuthenticated().has_permission(request, self):
            return Response({"detail": "Authentication credentials were not provided."}, context={'request': request}, status=HTTP_403_FORBIDDEN)
        
        event_id = request.data.get('event')
        user = request.user
        try:
            event = KetchupEvent.objects.get(id=event_id)
        except KetchupEvent.DoesNotExist:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)
        if request.user == event.user:
            return Response({"error": "Event creators cannot submit applications."}, status=status.HTTP_400_BAD_REQUEST)
        
        # limit duplicating applications
        existing_application = Application.objects.filter(user=user, event_id=event_id).first()
        if existing_application:
            return Response({"error": "You have already applied for this KetchupEvent."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ApplicationSerializer( data=request.data, context={'request': request})
        if serializer.is_valid():
            reception_list = event.user.email

            if user.firstname:
                applicant_name = user.firstname
                if user.lastname:
                    applicant_name = applicant_name + " " + user.lastname
            elif user.lastname:
                 applicant_name = user.lastname
            else:
                applicant_name = user.username

            if event.user.firstname:
                receiver_name = event.user.firstname
                if event.user.lastname:
                    receiver_name = receiver_name + " " + event.user.lastname
            elif event.user.lastname:
                receiver_name = event.user.lastname
            else:
                receiver_name = event.user.username
            subject = f"New Application to your ketchup-event from {applicant_name}"
            message = f"Dear {receiver_name},\n\nYou have a new application from {applicant_name} to the ketchup {event.name}, check out more detail on Ketchup! \n\n\n(Do not reply to this email)"
            serializer.save(user=request.user)
            send_email(reception_list, subject, message)
            return Response({"message": "Application sent"}, status=HTTP_201_CREATED)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
    
class ApplicationDecisionAPIView(APIView):
    def post(self, request):
        application_id = request.data.get('id')
        new_status = request.data.get('status')

        if not application_id or new_status not in ApplicationStatus.values:
            return Response({"error": "Invalid request."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            application = Application.objects.get(id=application_id)
        except Application.DoesNotExist:
            return Response({"error": "Application not found."}, status=status.HTTP_404_NOT_FOUND)

        # check if the user is organizer
        if request.user != application.event.user:
            return Response({"error": "You are not authorized to update this Application."}, status=status.HTTP_403_FORBIDDEN)

        # parse the new status in request
        if new_status not in ApplicationStatus.values:
            return Response({"error": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

        # updating the status
        application.status = new_status
        application.save()

        if application.user.firstname:
            applicant_name = application.user.firstname
            if application.user.lastname:
                applicant_name = applicant_name + " " + application.user.lastname
        elif application.user.lastname:
             applicant_name = application.user.lastname
        else:
            applicant_name = application.user.username

        reception_list = application.user.email
        subject = f"Application status updated"
        message = f"Dear {applicant_name},\n\nYour application to the ketchup {application.event.name} is updated, the application is: {new_status},\n check out more detail on Ketchup! \n\n\n(Do not reply to this email)"
        send_email(reception_list, subject, message)

        return Response(ApplicationSerializer(application, context={'request': request} ).data, status=status.HTTP_202_ACCEPTED)

    
class InterestAPIView(APIView):
    # GET for everyone, POST for authenticated users only
    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [permissions.IsAuthenticated,]
        else:
            self.permission_classes = [permissions.AllowAny,]
        return super(InterestAPIView, self).get_permissions()

    def get(self, request, *args, **kwargs):
        interests = Interest.objects.all()
        serializer = InterestSerializer(interests, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = InterestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class MessageAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        messages = Message.objects.filter(Q(sender=user) | Q(receiver=user)).order_by('id')
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)
    
    def post(self, request):
        user = request.user
        receiver_id = request.data.get('receiver')
        message_content = request.data.get('message')
        datetime = timezone.now()
        
        if not receiver_id or message_content is None:
            return Response({"detail": "Receiver ID and message content are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            receiver =  User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=HTTP_404_NOT_FOUND)
        
        if user.role  == AccountRoles.USER:
            if user.firstname:
                sender_name = user.firstname
            else:
                sender_name = user.username
        elif user.role  == AccountRoles.BUSINESS:
            sender_name = user.name
        
        mail_content = f"Sender: {sender_name},\n\n{message_content} \n\n  (Check out message on Ketchup) \n\n\n(Do not reply to this email)"
        recipient_list = [receiver.email]
        subject = f"New Message from {sender_name} on Ketchup"
        # send_email(recipient_list, subject, mail_content)
        message = Message(sender=user, receiver=receiver, message=message_content, datetime=datetime)
        message.save()
        
        serializer = MessageSerializer(message, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class BusinessUserView(APIView):
    def get(self, request, format=None):
        business_users = User.objects.filter(role='business')
        # handle interest list filtering
        interests = request.query_params.getlist('interests')
        for interest in interests:
            business_users = business_users.filter(business_profile__interests=interest).distinct()
        serializer = UserSerializer(business_users, context={'request': request}, many=True)
        return Response(serializer.data)

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # see more on https://www.django-rest-framework.org/api-guide/permissions/
    permission_classes = [permissions.AllowAny]

class UserView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, format=None):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True, context={'request': request})
        return Response(serializer.data, status=HTTP_200_OK)


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.AllowAny]