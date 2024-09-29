from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)

class Interest(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

PRIVACY_LEVELS = (
    ('private', 'Private'),
    ('openToGroup', 'Open to Group'),
    ('public', 'Public'),
)
class User(AbstractBaseUser):
    USER_ROLES = [
        ('user', 'User'),
        ('business', 'Business'),
        # TODO: Consider adding 'admin' if there's a need to differentiate superusers
    ]
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    email_verified = models.BooleanField(default=False)
    firstname = models.CharField(max_length=100, null=True)
    lastname = models.CharField(max_length=100, null=True)
    role = models.CharField(max_length=10, choices=USER_ROLES, default='user')
    interests = models.ManyToManyField(Interest, related_name='interests_of_user')
    avatar = models.ImageField(upload_to='user_avatars/', null=True, blank=True)
    privacy_level = models.CharField(max_length=12, choices=PRIVACY_LEVELS, default='private')
    bio = models.TextField(max_length=1024*5, null=True, blank=True, default='')
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email','password', 'firstname', 'lastname']
    objects = UserManager()

    # profile , interests used for filtering event list


    def __str__(self) -> str:
        return f'{self.username} : {self.email}'
    
class BusinessProfile(AbstractBaseUser):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business_profile')
    name = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=1024, null=True)
    description = models.TextField(max_length=1024*5, null=True, blank=True)
    interests = models.ManyToManyField(Interest, related_name='interests_of_business')
    phone_number = models.CharField(max_length=20, null=True)
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='business_images/', null=True, blank=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    starting_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    TYPE_CHOICES = (
        ('retail', 'Retail'),
        ('service', 'Service'),
        ('restaurant', 'Restaurant'),
        #  Add more types as needed
    )
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, null=True)
    opening_hours = models.TextField(help_text="Weekly timetable as text", null=True)

    def __str__(self) -> str:
        return self.name or self.user.username
    
class KetchupEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='organizer')
    business = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='business_of_event')
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100, null=True, blank=True, default='')
    datetime = models.DateTimeField(null=True, blank=True)
    description = models.CharField(max_length=1024*5, null=True, blank=True, default='')
    interests = models.ManyToManyField(Interest, related_name='interests_of_event')
    image = models.ImageField(upload_to='ketchup_events_images/', null=True, blank=True)
    # maxMemberCount = models.IntegerField(max_value=10, min_value=2)
    # estimatedDuration = models.IntegerField(max_value=120, min_value=10)
    maxMemberCount = models.PositiveIntegerField(default=5, validators=[MinValueValidator(2), MaxValueValidator(10)])
    estimatedDuration = models.PositiveIntegerField(default=60, validators=[MinValueValidator(30), MaxValueValidator(180)])

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='message_sender')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='message_receiver')
    message = models.CharField(max_length=1024*5, null=True, blank=True, default='')
    datetime = models.DateTimeField(null=True, blank=True)

class ApplicationStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    ACCEPTED = 'accepted', _('Accepted')
    REJECTED = 'rejected', _('Rejected')

class AccountRoles(models.TextChoices):
    USER = 'user', _('User')
    BUSINESS = 'business', _('Business')

class Application(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(KetchupEvent, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING,
    )


# class ketchup():