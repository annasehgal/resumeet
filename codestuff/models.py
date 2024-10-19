import os
import uuid

from django.contrib.auth.models import User

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q, Max
from django.dispatch import receiver
from django.forms import models
from django.template.defaultfilters import slugify
from django.urls import reverse, reverse_lazy

from django.db import models
from django.views.generic import CreateView

STATES = [
    ('AL', 'Alabama'),
    ('AK', 'Alaska'),
    ('AZ', 'Arizona'),
    ('AR', 'Arkansas'),
    ('CA', 'California'),
    ('CO', 'Colorado'),
    ('CT', 'Connecticut'),
    ('DE', 'Delaware'),
    ('FL', 'Florida'),
    ('GA', 'Georgia'),
    ('HI', 'Hawaii'),
    ('ID', 'Idaho'),
    ('IL', 'Illinois'),
    ('IN', 'Indiana'),
    ('IA', 'Iowa'),
    ('KS', 'Kansas'),
    ('KY', 'Kentucky'),
    ('LA', 'Louisiana'),
    ('ME', 'Maine'),
    ('MD', 'Maryland'),
    ('MA', 'Massachusetts'),
    ('MI', 'Michigan'),
    ('MN', 'Minnesota'),
    ('MS', 'Mississippi'),
    ('MO', 'Missouri'),
    ('MT', 'Montana'),
    ('NE', 'Nebraska'),
    ('NV', 'Nevada'),
    ('NH', 'New Hampshire'),
    ('NJ', 'New Jersey'),
    ('NM', 'New Mexico'),
    ('NY', 'New York'),
    ('NC', 'North Carolina'),
    ('ND', 'North Dakota'),
    ('OH', 'Ohio'),
    ('OK', 'Oklahoma'),
    ('OR', 'Oregon'),
    ('PA', 'Pennsylvania'),
    ('RI', 'Rhode Island'),
    ('SC', 'South Carolina'),
    ('SD', 'South Dakota'),
    ('TN', 'Tennessee'),
    ('TX', 'Texas'),
    ('UT', 'Utah'),
    ('VT', 'Vermont'),
    ('VA', 'Virginia'),
    ('WA', 'Washington'),
    ('WV', 'West Virginia'),
    ('WI', 'Wisconsin'),
    ('WY', 'Wyoming'),
]


class Major(models.Model):
    major = models.CharField(max_length=200)
    population = models.IntegerField(default=0)

    def __str__(self):
        return str(self.major)

    class Meta:
        verbose_name = "Major"


class Keywords(models.Model):
    keyword = models.CharField(max_length=200)
    number_of_clicks = models.IntegerField(default=0)

    def __str__(self):
        return str(self.keyword)

    class Meta:
        verbose_name = "Keywords"
        verbose_name_plural = "Keywords"


def validate_dob(value):
    if value > timezone.now().date():
        raise ValidationError('Date of birth cannot be in the future.')


class PersonalProfile(models.Model):
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField(validators=[validate_dob])
    state = models.CharField(max_length=2, choices=STATES)
    city = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Personal Profile"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    # username = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='media', null=True, blank=True, verbose_name="Profile picture")
    alternate = models.TextField(verbose_name="Alternate text", blank=True, null=True)
    about_me = models.TextField(blank=True, null=True)
    keywords = models.ManyToManyField(Keywords)
    opt_in = models.BooleanField(default=False)
    position = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Position for sorting",
    )
    # link_to_profile = models.URLField(default=1, blank=True, null=True, verbose_name="Link to profile") #possibly consider making this automatically fill with the link to the user's profile
    # consider making a randomized pk that is assigned to each invididual user and can be attached to the end of the default profile url like in this schema: "http://127.0.0.1:8000/profile/pk/
    is_active = models.IntegerField(default=1,
                                    blank=True,
                                    null=True,
                                    help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")

    def __str__(self):
        return str(self.user)

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse('profile', kwargs={'username': self.username})

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.user.username

        super().save(*args, **kwargs)

    def get_profile_url(self):
        profile = Profile.objects.filter(user=self.user).first()
        if profile:
            return reverse('profile', args=[str(profile.pk)])

    class Meta:
        verbose_name = "Account Profile"
        verbose_name_plural = "Account Profiles"


class InternProfile(models.Model):
    username = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=True, null=True)
    major = models.ForeignKey(Major, on_delete=models.CASCADE)
    resume = models.FileField(blank=True, null=True)

    is_active = models.IntegerField(
        default=1,
        blank=True,
        null=True,
        help_text='1->Active, 0->Inactive',
        choices=((1, 'Active'), (0, 'Inactive')),
        verbose_name="Set active?"
    )

    def __str__(self):
        return str(self.username + " - " + str(self.major))

    class Meta:
        verbose_name = "Intern Profile"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('profile', kwargs={'pk': self.pk})  # or 'username' if it remains

    def save(self, *args, **kwargs):
        # Set the user if not already assigned
        if not self.user:
            self.user = kwargs.pop('current_user', None)
            if not self.user:
                raise ValueError('User must be provided')

        # Set the profile if not already assigned
        if not self.profile and self.user:
            # Check if the user has a profile before accessing it
            if hasattr(self.user, 'profile'):
                self.profile = self.user.profile
            else:
                # Create a new Profile if it doesn't exist
                self.profile = Profile.objects.create(user=self.user)
                print(f"Profile created for {self.user}")

        # Set the username if not already assigned
        if not self.username and self.user:
            self.username = self.user.username

        # Save the instance
        super().save(*args, **kwargs)


class LandingImage(models.Model):
    image = models.ImageField(upload_to='media')
    name = models.CharField(max_length=200, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Check if the name field is empty
        if not self.name:
            # Get the original filename from the image field
            self.name = os.path.splitext(os.path.basename(self.image.name))[0]  # Extract the filename without the extension
        super().save(*args, **kwargs)  # Call the parent save method

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Landing Image"


class Community(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='communities')
    created_at = models.DateTimeField(auto_now_add=True)
    logo = models.FileField(blank=True, null=True, verbose_name="Logo")
    public = models.BooleanField(default=False)
    members = models.ManyToManyField(User, related_name='member')
    is_active = models.IntegerField(
        default=1,
        blank=True,
        null=True,
        choices=((1, 'Active'), (0, 'Inactive')),
        verbose_name="Set active?"
    )

    def __str__(self):
        return self.name

    def get_invite_link(self):
        return reverse('community_invite', kwargs={'invite_token': self.invite_token})

    def save(self, *args, **kwargs):
        creating = self.pk is None  # Check if this is a new instance
        if self.owner is None:
            self.owner = self.created_by
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)  # Call the original save method

        # Automatically create a related Room when a new Community is created
        if creating:
            Room.objects.create(
                community=self,
                name=self.name,
                signed_in_user=self.created_by,
                public=self.public  # Set public to the same as the community's public field
            )

    class Meta:
        verbose_name_plural = 'Communities'


class Role(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=200)
    ability_to_add_rooms = models.BooleanField(default=False)
    ability_to_add_people = models.BooleanField(default=True)
    ability_to_kick_people = models.BooleanField(default=False)
    ability_to_ban_people = models.BooleanField(default=False)
    ability_to_assign_roles = models.BooleanField(default=False)
    hierarchy = models.IntegerField(blank=True, null=True)
    administrator = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Automatically set the hierarchy value if it's not provided
        if self.hierarchy is None:
            # Find the current highest hierarchy in the same community
            highest_hierarchy = Role.objects.filter(community=self.community).aggregate(
                max_hierarchy=models.Max('hierarchy')
            )['max_hierarchy']

            # Set to 1 if no roles exist in the community, otherwise increment the max by 1
            self.hierarchy = (highest_hierarchy or 0) + 1

        # If administrator is set to True, set all other privileges to True
        if self.administrator:
            self.ability_to_add_rooms = True
            self.ability_to_add_people = True
            self.ability_to_kick_people = True
            self.ability_to_ban_people = True
            self.ability_to_assign_roles = True

        # Call the original save method to save the changes
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} in {self.community.name}"


# Through model for assigning roles to users in a community
class CommunityRoleAssignment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_roles')
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_assignments')
    assigned_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'community', 'role')

    def __str__(self):
        return f"{self.user.username} as {self.role.name} in {self.community.name}"


class Room(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='rooms')
    name = models.CharField(max_length=1000)
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True)
    signed_in_user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='rooms_created', verbose_name="Room Creator")
    members = models.ManyToManyField(User, blank=True, related_name="room_members")
    time = models.DateTimeField(default=timezone.now, blank=True)
    public = models.BooleanField(default=False, verbose_name="Make Public?")
    logo = models.FileField(blank=True, null=True, verbose_name="Logo")
    is_active = models.IntegerField(
        default=1,
        blank=True,
        null=True,
        choices=((1, 'Active'), (0, 'Inactive')),
        verbose_name="Set active?"
    )

    def __str__(self):
        return self.name if self.name else 'Guest'

    def save(self, *args, **kwargs):
        if not self.slug:
            print("Name:", self.name)  # Print the title
            self.slug = slugify(self.name)
            print("Slug after slugify:", self.slug)  # Print the slug after slugify

        if not self.pk:
            # Get the associated Profile for the user
            profile = Profile.objects.filter(user=self.user).first()

        super().save(*args, **kwargs)

    def user_can_join(self, user):
        if self.public:
            return True
        if user.is_authenticated:
            # Allow the room creator to join the room
            if self.signed_in_user == user:
                return True
            # Check if there's an accepted friend request between the user and the room creator
            return FriendRequest.objects.filter(
                Q(sender=self.signed_in_user, receiver=user, status=FriendRequest.ACCEPTED) |
                Q(sender=user, receiver=self.signed_in_user, status=FriendRequest.ACCEPTED)
            ).exists()
        return False


class Message(models.Model):
    value = models.CharField(max_length=1000000)
    date = models.DateTimeField(default=timezone.now, blank=True)
    user = models.CharField(max_length=1000000, verbose_name="Username")
    signed_in_user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='messages',
                                       verbose_name="User")
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    message_number = models.PositiveIntegerField(default=0, editable=False)
    file = models.FileField(upload_to='media/', null=True, blank=True)
    image_length = models.PositiveIntegerField(blank=True, null=True, default=100,
                                               help_text='Original length of the advertisement (use for original ratio).',
                                               verbose_name="image length")
    image_width = models.PositiveIntegerField(blank=True, null=True, default=100,
                                              help_text='Original width of the advertisement (use for original ratio).',
                                              verbose_name="image width")
    is_active = models.IntegerField(default=1, blank=True, null=True, help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")

    def __str__(self):
        if self.value:
            return f"{self.value} in {self.room}"
        else:
            return f"blank message in {self.room}"

    def save(self, *args, **kwargs):
        if not self.pk:
            # Get the current maximum message number
            max_message_number = Message.objects.aggregate(max_message_number=Max('message_number'))[
                                     'max_message_number'] or 0
            # Increment the maximum message number to get the new message number
            self.message_number = max_message_number + 1

            # Get the associated Profile for the donor
            profile = Profile.objects.filter(user=self.signed_in_user).first()

            # Set the position to the position value from the associated Profile if it exists
            if profile and hasattr(self, 'position'):
                self.position = profile.position

        super().save(*args, **kwargs)

        # Update the Friend instances associated with the signed_in_user and friend fields
        if self.signed_in_user and self.room:
            # Get the Friend instances associated with the signed_in_user and friend fields
            friends = Friend.objects.filter(
                (Q(user=self.signed_in_user) & Q(friend__username=self.room)) |
                (Q(user__username=self.room) & Q(friend=self.signed_in_user))
            )

            # Update the Friend instances with the latest message and the date
            for friend in friends:
                friend.latest_messages = self
                friend.last_messaged = self.date
                friend.save(update_fields=['latest_messages', 'last_messaged'])

    def get_profile_url(self):
        profile = Profile.objects.filter(user=self.signed_in_user).first()
        if profile:
            return reverse('profile', args=[str(profile.pk)])

    def get_absolute_url(self):
        # Construct the URL for the room detail page
        room_url = reverse("room", kwargs={'room': str(self.room)})
        # Construct the query parameters
        final_url = f"{room_url}?username={self.signed_in_user.username}"
        return final_url


def get_friends(self):
    from .models import FriendRequest  # Import here to avoid circular import
    accepted_friend_requests = FriendRequest.objects.filter(
        Q(sender=self, status=FriendRequest.ACCEPTED) | Q(receiver=self, status=FriendRequest.ACCEPTED))
    friends = set()
    for friend_request in accepted_friend_requests:
        if friend_request.sender == self:
            friends.add(friend_request.receiver)
        else:
            friends.add(friend_request.sender)
    print('friends here')
    return friends


#change to newsletter
class NewsLetter(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100,
                            help_text='Your name and tag go here. If you wish to stay anonymous, put "Anonymous".')
    title = models.TextField(help_text='Write the news headline here.', verbose_name="News Headline")
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True)
    category = models.CharField(max_length=200, help_text='Please let us know what form of news this is.')
    description = models.TextField(help_text='Write the news here.')
    image = models.ImageField(help_text='Please provide a cover image for the news.')
    image_length = models.PositiveIntegerField(blank=True, null=True, default=100,
                                               help_text='Original length of the advertisement (use for original ratio).',
                                               verbose_name="image length")
    image_width = models.PositiveIntegerField(blank=True, null=True, default=100,
                                              help_text='Original width of the advertisement (use for original ratio).',
                                              verbose_name="image width")
    date_and_time = models.DateTimeField(null=True, verbose_name="time and date", auto_now_add=True)
    position = models.IntegerField(verbose_name="Image Position", default=1)
    anonymous = models.BooleanField(default=False, help_text="Remain anonymous? (not recommended)")
    is_active = models.IntegerField(default=1,
                                    blank=True,
                                    null=True,
                                    help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")

    def __str__(self):
        return self.title + " authored by " + str(self.user)

    class Meta:
        verbose_name = "News Feed"
        verbose_name_plural = "News Feed"

    def save(self, *args, **kwargs):
        if not self.slug:
            print("Name:", self.name)  # Print the title
            self.slug = slugify(self.name)
            print("Slug after slugify:", self.slug)  # Print the slug after slugify

        if not self.pk:
            # Get the associated Profile for the user
            profile = Profile.objects.filter(user=self.user).first()

            # Set the position to the position value from the associated Profile
            # if profile:
            # self.position = profile.position


        print("Position before save:", self.position)
        super().save(*args, **kwargs)

    # def get_absolute_url(self):

    # return reverse("news", kwargs={"slug": str(self.slug)})

    def get_profile_url(self):
        profile = Profile.objects.filter(user=self.user).first()
        if profile:
            return reverse('profile', args=[str(profile.pk)])

    def get_profile_url2(self):
        news = NewsLetter.objects.filter(user=self.user, slug=self.slug).first()
        if news:
            return reverse('singlenews', args=[str(news.slug)])


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    mfg_date = models.DateTimeField(auto_now_add=True, verbose_name="date")
    opt_in = models.BooleanField(default=False)
    is_active = models.IntegerField(default=1,
                                    blank=True,
                                    null=True,
                                    help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"


class FriendRequest(models.Model):
    PENDING = 0
    ACCEPTED = 1
    DECLINED = 2

    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (DECLINED, 'Declined'),
    )

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status = models.IntegerField(choices=STATUS_CHOICES, default=PENDING)

    def __str__(self):
        return f'{self.sender.username} -> {self.receiver.username}: {self.get_status_display()}'

    def get_friend_profile_pic(self):
        return self.friend.Profile.profile_pic.url if self.friend.Profile.profile_pic else None

    def get_user_profile_pic(self):
        return self.user.Profile.profile_pic.url if self.user.Profile.profile_pic else None

    def get_profile_url(self, current_user):
        if current_user == self.sender or current_user == self.receiver:
            profile = Profile.objects.filter(user=current_user).first()
            if profile:
                return reverse('profile', args=[str(profile.pk)])

    # Handle the case where the current user is neither the sender nor the receiver

    class Meta:
        verbose_name = "Friend Request"
        verbose_name_plural = "Friend Requests"
        unique_together = ('sender', 'receiver')


class Friend(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friends')
    friend_username = models.CharField(max_length=500, blank=True, null=True)
    latest_messages = models.ForeignKey(Message, blank=True, null=True, on_delete=models.CASCADE)
    last_messaged = models.DateTimeField(blank=True, null=True)
    currently_active = models.BooleanField(default=False)  # are you currently on the person's chat profile
    created_at = models.DateTimeField(auto_now_add=True)
    online = models.BooleanField(default=False)
    is_active = models.IntegerField(default=1,
                                    blank=True,
                                    null=True,
                                    help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")

    def __str__(self):
        return str(self.user) + " is friends with " + str(self.friend) + "!"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Call the original save method first
        if self.currently_active:
            # Update the currently_active field for all instances with the same user field, except for this instance
            Friend.objects.exclude(pk=self.pk).filter(user=self.user).update(currently_active=False)
        self.friend_username = self.friend.username
        latest_message_queryset = Message.objects.filter(Q(signed_in_user=self.user) | Q(signed_in_user=self.friend))

        latest_message = latest_message_queryset.order_by('-date').first()
        if latest_message:
            self.latest_messages = latest_message
            self.last_messaged = latest_message.date
        super().save(*args, **kwargs)  # Save the model again with the updated field (optional)

    def get_profile_url(self):
        profile = Profile.objects.filter(user=self.user).first()
        if profile:
            return reverse('profile', args=[str(profile.pk)])

    def get_profile_url2(self):
        # If friend_username is None, return the base 'new_chat' URL
        if self.friend_username is None:
            return reverse("new_chat")

        # If friend_username exists, use it for the new_chat_create view
        room_url = reverse("new_chat_create", kwargs={'username': self.friend_username})

        # Construct the query parameters with the username
        final_url = f"{room_url}?username={self.user.username}"

        return final_url


class Meta:
    unique_together = ('user', 'friend')


class Event(models.Model):
    event = models.CharField(max_length=200)
    host = models.ForeignKey(User, on_delete=models.CASCADE)
    participants = models.ManyToManyField(User, related_name='participant')
    is_active = models.IntegerField(
        default=1,
        blank=True,
        null=True,
        choices=((1, 'Active'), (0, 'Inactive')),
        verbose_name="Set active?"
    )


class NotificationType(models.Model):
    """Model to define different types of notifications."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Notification(models.Model):
    """Custom Notification model."""
    recipient_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    message = models.TextField()  # The content of the notification
    timestamp = models.DateTimeField(auto_now_add=True)  # Automatically set the time when the notification is created
    is_read = models.BooleanField(default=False)  # To track if the notification has been read

    class Meta:
        app_label = 'codestuff'  # Specify the app where this model is located
        ordering = ['-timestamp']  # Orders notifications by newest first

    def __str__(self):
        return f"Notification to {self.recipient_user.username} - {self.notification_type.name}"


class About(models.Model):
    about_us = models.TextField()

    class Meta:
        verbose_name = "About Us"
        verbose_name_plural = "About Us"


class SupportEmail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    message = models.TextField()


class DefaultAvatar(models.Model):
    default_avatar_name = models.CharField(max_length=300, blank=True, null=True)
    default_avatar = models.ImageField(upload_to='images/')
    is_active = models.IntegerField(default=1,
                                    blank=True,
                                    null=True,
                                    help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")

    def __str__(self):
        if self.default_avatar_name:
            return str(self.default_avatar_name)

    def save(self, *args, **kwargs):
        if not self.default_avatar_name and self.default_avatar:
            self.default_avatar_name = self.default_avatar.name
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Default Avatar"
        verbose_name_plural = "Default Avatars"
