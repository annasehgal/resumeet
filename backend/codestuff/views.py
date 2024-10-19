from venv import logger

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db.models.signals import post_save
from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import FormMixin, CreateView

from .models import Message, FriendRequest, Friend, Subscription, PersonalProfile, \
    InternProfile, Notification, Event, About, SupportEmail, LandingImage, \
    DefaultAvatar, NewsLetter  # Adjust the import path if necessary
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.checks import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import ListView, TemplateView, DetailView

from codestuff.forms import UserCreateForm, EmailForm, CommunityForm, ProfileForm, PersonalProfileForm, \
    InternProfileForm, SupportEmailForm, RSVPForm, FriendRequestForm
from codestuff.models import Room, Message, Profile, Community


from django.views.decorators.http import require_http_methods
from django.utils import timezone

from django.shortcuts import render

from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from .models import Room, Message, Profile, DefaultAvatar

@require_http_methods(["GET", "POST"])
def getMessages(request, slug, room):
    try:
        room_details = Room.objects.get(slug=slug, name=room)  # Assuming 'slug' is used to identify the room
    except Room.DoesNotExist:
        return render(request, '404.html', {'error': 'Room does not exist'}, status=404)

    if request.method == "POST":
        # Extract message data from the request
        message_content = request.POST.get('value')
        user = request.user

        # Create a new message
        message = Message.objects.create(
            room=room_details,
            signed_in_user=user,
            value=message_content,
            date=timezone.now()
        )

        # Redirect to the messages view (to render updated messages)
        return redirect('get_messages', slug=slug, room=room)  # Redirect to the same view

    # If GET request, return existing messages
    messages = Message.objects.filter(room=room_details)
    messages_data = []

    for message in messages:
        if message.signed_in_user:
            user_profile_url = message.get_profile_url()
            username = message.signed_in_user.username
            try:
                profile_details = Profile.objects.get(user=message.signed_in_user)
                avatar_url = profile_details.avatar.url if profile_details.avatar else None
            except Profile.DoesNotExist:
                avatar_url = DefaultAvatar.objects.first().url if DefaultAvatar.objects.exists() else None
        else:
            user_profile_url = f'/community/{slug}/?username=Unknown'
            username = "Unknown User"
            avatar_url = DefaultAvatar.objects.first().url if DefaultAvatar.objects.exists() else None

        messages_data.append({
            "user_profile_url": user_profile_url,
            "avatar_url": avatar_url,
            "value": message.value,
            "date": message.date.strftime("%Y-%m-%d %H:%M:%S"),
            "message_number": message.message_number,
            "file": message.file.url if message.file else None,
            "username": username,
        })

    return render(request, 'room.html', {'room': room_details, 'messages': messages_data})


def signup(request):
    form = UserCreateForm()

    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            user = User.objects.get(username=request.POST['username'])
            profile = Profile(user=user)
            profile.save()

            new_user = authenticate(username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password1'])
            login(request, new_user)
            return redirect('index')

    return render(request, 'signup.html', {
        'form': form
    })


from django.shortcuts import get_object_or_404

from django.http import Http404
from django.views.generic import ListView
from .models import Community, Profile


class CommunityView(ListView):
    model = Community
    template_name = 'community_index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs['slug']  # Use 'slug' for the community slug
        username = self.request.GET.get('username')

        # Query the Community using the slug
        try:
            community_details = Community.objects.get(slug=slug)
        except Community.DoesNotExist:
            raise Http404("Community does not exist")

        # Fetch the profile details of the user (if provided)
        profile_details = Profile.objects.filter(user__username=username).first()

        # Query the members of the community and their profiles
        member_profiles = Profile.objects.filter(user__in=community_details.members.all())

        # Add additional context for roles, rooms, and user role assignments
        context['username'] = username
        context['room'] = slug
        context['community_details'] = community_details
        context['profile_details'] = profile_details
        context['member_profiles'] = member_profiles

        # Adding roles and user role assignments
        context['roles'] = community_details.roles.all()
        context['rooms'] = community_details.rooms.all()
        context['user_roles'] = community_details.user_roles.all()

        slug = self.kwargs['slug']  # Use 'slug' for the community slug

        try:
            community_details = Community.objects.get(slug=slug)
        except Community.DoesNotExist:
            raise Http404("Community does not exist")

        print(f"Community Slug: {community_details.slug}")  # Debugging line

        # Fetch the profile details of the user (if provided)

        # Query the members of the community and their profiles
        member_profiles = Profile.objects.filter(user__in=community_details.members.all())

        # Add additional context for roles, rooms, and user role assignments
        context['room'] = slug
        context['community'] = community_details  # Ensure you're passing this to the template
        context['member_profiles'] = member_profiles

        # Adding roles and user role assignments
        context['roles'] = community_details.roles.all()
        context['rooms'] = community_details.rooms.all()
        context['user_roles'] = community_details.user_roles.all()

        return context


class RoomView(ListView):
    model = Room
    template_name = 'room.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room_name = self.kwargs['room']  # Use 'room' from the URL as the room's name

        # Query the Room using the name
        try:
            room_details = Room.objects.get(name=room_name)
        except Room.DoesNotExist:
            raise Http404("Room does not exist")

        username = self.request.GET.get('username')
        profile_details = Profile.objects.filter(user__username=username).first()

        context['username'] = username
        context['room'] = room_name
        context['room_details'] = room_details
        context['profile_details'] = profile_details

        # Fetch messages related to the room and order by date
        messages = Message.objects.filter(room=room_details).order_by('-date')
        context['Messaging'] = messages

        # Add user profile picture URLs to each message, if available
        for message in context['Messaging']:
            profile = Profile.objects.filter(user=message.signed_in_user).first()
            if profile:
                message.user_profile_picture_url = profile.avatar.url
                message.user_profile_url = profile.get_absolute_url()

        return context



@login_required
def kick_user_view(request, community_id, user_id):
    community = get_object_or_404(Community, id=community_id)
    user_to_kick = get_object_or_404(User, id=user_id)

    message = community.kick_user(user_to_kick, request.user)
    messages.info(request, message)

    return redirect('community', community_id=community.id)


@login_required
def ban_user_view(request, community_id, user_id):
    community = get_object_or_404(Community, id=community_id)
    user_to_ban = get_object_or_404(User, id=user_id)

    message = community.ban_user(user_to_ban, request.user)
    messages.info(request, message)

    return redirect('community', community_id=community.id)


# This function handles changes in FriendRequest status.
@receiver(post_save, sender=FriendRequest)
def handle_friend_request(sender, instance, created, **kwargs):
    if instance.status == FriendRequest.ACCEPTED:
        # Create mutual friendship (both directions)
        Friend.objects.get_or_create(user=instance.sender, friend=instance.receiver)
        Friend.objects.get_or_create(user=instance.receiver, friend=instance.sender)
    elif instance.status == FriendRequest.DECLINED:
        # Delete the friendships if they exist (both directions)
        Friend.objects.filter(
            Q(user=instance.sender, friend=instance.receiver) |
            Q(user=instance.receiver, friend=instance.sender)
        ).delete()

# Connect the signal to post_save of FriendRequest model
post_save.connect(handle_friend_request, sender=FriendRequest)

# This function updates the friend_username field after saving a Friend instance.
@receiver(post_save, sender=Friend)
def update_friend_username(sender, instance, created, **kwargs):
    # Update friend_username with the friend's username
    instance.friend_username = instance.friend.username
    instance.save(update_fields=['friend_username'])  # Update only the specific field to avoid a full save.

# Connect the signal to post_save of Friend model
post_save.connect(update_friend_username, sender=Friend)


class BackgroundView(FormMixin, ListView):
    model = Subscription
    form_class = EmailForm
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context



def login_user(request):
    # Your login logic here
    return render(request, 'login.html')


class CreateCommunityView(LoginRequiredMixin, View):
    def get(self, request):
        form = CommunityForm()
        return render(request, 'codestuff/create_community.html', {'form': form})

    def post(self, request):
        form = CommunityForm(request.POST, request.FILES)  # Handle file upload
        if form.is_valid():
            community = form.save(commit=False)
            community.owner = request.user  # Set the owner to the current user
            community.created_by = request.user  # Set created_by to the current user
            community.save()
            return redirect('community', pk=community.pk)  # Redirect to the community detail page
        return render(request, 'codestuff/create_community.html', {'form': form})


class UserCommunitiesView(LoginRequiredMixin, View):
    def get(self, request):
        communities = request.user.communities_joined.all()  # Get communities the user is a member of
        return render(request, 'codestuff/user_communities.html', {'communities': communities})


class FriendView(ListView):
    model = Friend
    template_name = 'friendslist.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        signed_in_user = self.request.user

        if signed_in_user.is_authenticated:
            context['user_profile'] = Profile.objects.filter(user=signed_in_user).first()
            context['friends'] = Friend.objects.filter(user=signed_in_user)
        return context


class FriendSearchResultsView(ListView):
    model = Friend
    template_name = 'friendslist.html'
    context_object_name = 'friends'

    def get_queryset(self):
        search_term = self.request.GET.get('search', '')
        if search_term:
            friends = Friend.objects.filter(friend__username__icontains=search_term)
        else:
            friends = Friend.objects.filter(user=self.request.user)

        # Return a distinct set of friends
        distinct_friends = []
        seen_friends = set()

        for friend in friends:
            if friend.friend not in seen_friends:
                distinct_friends.append(friend)
                seen_friends.add(friend.friend)

        return distinct_friends

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('search', '')
        return context

    def friend_search(self, request):
        search_term = request.GET.get('search', '')
        if search_term:
            friends = Friend.objects.filter(friend__username__icontains=search_term)
        else:
            friends = Friend.objects.filter(user=request.user)

        # Use a distinct set of friends
        distinct_friends = []
        seen_friends = set()

        for friend in friends:
            if friend.friend not in seen_friends:
                distinct_friends.append(friend)
                seen_friends.add(friend.friend)

        if request.is_ajax():
            html = render_to_string('friendslist_results.html', {'friends': distinct_friends})
            return JsonResponse({'html': html})

        context = {
            'friends': distinct_friends,
            'search_term': search_term,
        }
        return render(request, 'friendslist.html', context)


def signup_success(request):
    return render(request, 'signup_success.html')


class ProfileView(DetailView):
    model = Profile
    template_name = 'profile.html'
    context_object_name = 'profile'

    def get_object(self):
        # Get the user by the username from the URL and return the corresponding profile
        user = get_object_or_404(User, username=self.kwargs['username'])
        return get_object_or_404(Profile, user=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['username'] = self.kwargs['username']
        signed_in_user = self.request.user

        if signed_in_user.is_authenticated:
            context['user_profile'] = Profile.objects.filter(user=signed_in_user).first()

        return context

# Profile Form View
class ProfileCreateView(CreateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'profile_form.html'  # Specify your template name
    success_url = reverse_lazy('profile_success')  # Redirect to a success page or another view


# Personal Profile Form View
class PersonalProfileCreateView(CreateView):
    model = PersonalProfile
    form_class = PersonalProfileForm
    template_name = 'personal_profile_form.html'  # Specify your template name
    success_url = reverse_lazy('personal_profile_success')  # Redirect after submission


# Intern Profile Form View
class InternProfileCreateView(CreateView):
    model = InternProfile
    form_class = InternProfileForm
    template_name = 'intern_profile_form.html'  # Specify your template name
    success_url = reverse_lazy('intern_profile_success')  # Redirect after submission


# Profile Form View
def create_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('profile_success')  # Redirect after saving
    else:
        form = ProfileForm()
    return render(request, 'profile_form.html', {'form': form})


# Personal Profile Form View
def create_personal_profile(request):
    if request.method == 'POST':
        form = PersonalProfileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('personal_profile_success')  # Redirect after saving
    else:
        form = PersonalProfileForm()
    return render(request, 'personal_profile_form.html', {'form': form})


# Intern Profile Form View
def create_intern_profile(request):
    if request.method == 'POST':
        form = InternProfileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('intern_profile_success')  # Redirect after saving
    else:
        form = InternProfileForm()
    return render(request, 'intern_profile_form.html', {'form': form})


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/notification_list.html'  # Specify your template
    context_object_name = 'notifications'
    paginate_by = 10  # Number of notifications per page, if pagination is needed

    def get_queryset(self):
        # Get notifications for the logged-in user
        return Notification.objects.filter(recipient_user=self.request.user).order_by('-timestamp')


class EventView(ListView):
    model = Event
    template_name = "events.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Events'] = Event.objects.all()

        newprofile = Event.objects.filter(is_active=1)
        # Retrieve the author's profile avatar

        context['Profiles'] = newprofile

        for newprofile in context['Profiles']:
            user = newprofile.user
            profile = Profile.objects.filter(user=user).first()
            if profile:
                newprofile.newprofile_profile_picture_url = profile.avatar.url
                newprofile.newprofile_profile_url = newprofile.get_profile_url()

        return context


class AboutView(ListView):
    model = About
    template_name = "about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Events'] = Event.objects.all()

        newprofile = Event.objects.filter(is_active=1)
        # Retrieve the author's profile avatar

        context['Profiles'] = newprofile

        for newprofile in context['Profiles']:
            user = newprofile.user
            profile = Profile.objects.filter(user=user).first()
            if profile:
                newprofile.newprofile_profile_picture_url = profile.avatar.url
                newprofile.newprofile_profile_url = newprofile.get_profile_url()

        return context


@login_required
def join_community(request, invite_token):
    # Get the community associated with the invite token
    community = get_object_or_404(Community, invite_token=invite_token, is_private=True)

    # Check if the user is already a member of the community
    if community.members.filter(id=request.user.id).exists():
        return HttpResponse("You are already a member of this community.")

    # Add the user to the community's members (assuming a many-to-many relationship with User)
    community.members.add(request.user)
    return redirect('community', community_id=community.id)  # Redirect to the community's detail page


class ChatView(ListView):
    model = Community
    template_name = "community.html"  # Update the template name to match
    context_object_name = 'community'

    def get_object(self):
        return get_object_or_404(Community, slug=self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        signed_in_user = self.request.user
        context['communityin'] = Community.objects.filter(is_active=True, members=signed_in_user)
        context['public_communities'] = Community.objects.filter(is_active=True, public=True)
        if self.request.user.is_authenticated:
            # Fetch user's friends
            context['Friends'] = Friend.objects.filter(user=self.request.user)

            current_user = self.request.user
            newprofile = Profile.objects.filter(is_active=1, user=current_user)
            context['Profiles'] = newprofile

            # Process profiles to add URLs and avatars
            for newprofile in context['Profiles']:
                user = newprofile.user
                profile = Profile.objects.filter(user=user).first()
                if profile:
                    newprofile.newprofile_profile_picture_url = profile.avatar.url
                    newprofile.newprofile_profile_url = newprofile.get_profile_url()

            # Fetch online profiles
            onlineprofile = Friend.objects.filter(is_active=1, user=current_user)
            context['OnlineProfiles'] = onlineprofile

            for onlineprofile in context['OnlineProfiles']:
                friend = onlineprofile.friend
                activeprofile = Profile.objects.filter(user=friend).first()
                if activeprofile:
                    onlineprofile.author_profile_picture_url = profile.avatar.url
                    onlineprofile.friend_profile_picture_url = activeprofile.avatar.url
                    onlineprofile.author_profile_url = onlineprofile.get_profile_url()
                    onlineprofile.friend_name = onlineprofile.friend.username
                    print('activeprofile exists')

            # Friends data with profiles
            friends = Friend.objects.filter(user=self.request.user)
            friends_data = []

            for friend in friends:
                profile = Profile.objects.filter(user=friend.friend).first()
                if profile:
                    friends_data.append({
                        'username': friend.friend.username,
                        'profile_picture_url': profile.avatar.url,
                        'profile_url': reverse('profile', args=[str(profile.pk)]),
                        'currently_active': friend.currently_active,
                        'user_profile_url': friend.get_profile_url2()
                    })

            context['friends_data'] = friends_data

            # Add the search functionality
            search_term = self.request.GET.get('search', '')
            if search_term:
                context = self.search_friends(context)

            # Add profiles (from the community function)
        else:
            # Provide default empty lists for anonymous users
            context['Friends'] = []
            context['Profiles'] = []
            context['OnlineProfiles'] = []
            context['friends_data'] = []
            context['search_results'] = []
            context['profiles'] = []  # From community logic

        return context

    def search_friends(self, context):
        search_term = self.request.GET.get('search', '')
        if search_term:
            item_list = Friend.objects.filter(
                Q(friend__username__icontains=search_term)
            ).prefetch_related('friend')

            search_results_data = []
            current_user = self.request.user

            for friend in item_list:
                profile = Profile.objects.filter(user=friend.friend).first()
                if profile:
                    search_results_data.append({
                        'username': friend.friend.username,
                        'profile_picture_url': profile.avatar.url if profile else None,
                        'profile_url': reverse('profile', args=[str(profile.pk)]),
                        'currently_active': friend.currently_active,
                    })
                    print('the friend does have a profile')
                else:
                    search_results_data.append({
                        'username': friend.friend.username,
                        'profile_picture_url': None,
                        'profile_url': reverse('profile', args=[str(friend.friend.pk)]),
                        'currently_active': friend.currently_active,
                    })
                    print('no profile on the friend')

            context['search_results'] = search_results_data
        else:
            context['search_results'] = []

        return context


@csrf_exempt
def send(request):
    if request.method == 'POST':
        message = request.POST.get('message')
        username = request.POST.get('username')
        room_id = request.POST.get('room_id')
        page_name = request.POST.get('page_name')

        if page_name == 'index.html':
            room_id = 'General'

        logger.debug(f"message: {message}, username: {username}, room_id: {room_id}, page_name: {page_name}")
        print(f"message: {message}, username: {username}, room_id: {room_id}, page_name: {page_name}")
        print('This is a community-sent message')

        try:
            room = Room.objects.get(name=room_id)
        except ObjectDoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Room does not exist.'})

        if not message:
            return JsonResponse({'status': 'error', 'message': 'Message is required.'})

        try:
            if request.user.is_authenticated:
                new_message = Message.objects.create(
                    value=message,
                    user=username,
                    room=room.name,
                    signed_in_user=request.user
                )
            else:
                new_message = Message.objects.create(
                    value=message,
                    user=username,
                    room=room.name
                )
            new_message.save()

            # Return only serializable data
            response_data = {
                'status': 'success',
                'message': 'Message sent successfully',
                'message_data': {
                    'value': new_message.value,
                    'user': new_message.user,
                    'room': new_message.room,
                    'file_url': new_message.file.url if new_message.file else None,
                    # You can include other fields that are JSON serializable
                }
            }

            return JsonResponse(response_data)
        except Exception as e:
            print(f"Error saving message: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


class SupportEmailView(CreateView):
    template_name = 'contact.html'
    form_class = SupportEmailForm
    success_url = reverse_lazy('showcase:success')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Contact'] = SupportEmail.objects.order_by('-id').first()
        print(context["Contact"])
        # context['TextFielde'] = TextBase.objects.filter(is_active=1,page=self.template_name).order_by("section")
        return context

    def form_valid(self, form):
        # Calls the custom send method
        form.send()
        return super().form_valid(form)


class ContactSuccessView(TemplateView):
    template_name = 'email.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(kwargs)
        context["Contact"] = "2123123123123"
        return context



class LandingImageView(ListView):
    model = LandingImage  # Specify the model to use
    template_name = 'index.html'  # Specify your template name
    context_object_name = 'landing_images'  # This will be used in the template

    def get_queryset(self):
        return LandingImage.objects.all()  # You can customize the queryset as needed


@login_required
def rsvp_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = RSVPForm(request.POST)
        if form.is_valid():
            event.participants.add(request.user)
            return redirect('event_detail', event_id=event.id)
    else:
        form = RSVPForm()

    return render(request, 'rsvp_event.html', {'event': event, 'form': form})


def community_detail(request, slug):
    community = get_object_or_404(Community, slug=slug)
    return render(request, 'community_detail.html', {'community': community})


class NewsView(ListView):
    model = NewsLetter
    template_name = 'news_list.html'  # The template where you will display the news
    context_object_name = 'news_list'  # This will be the context variable used in the template
    queryset = NewsLetter.objects.filter(is_active=1).order_by('-date_and_time')  # Only active news sorted by date
    paginate_by = 10  # Change to the number of items you want per page


class SingleNewsView(DetailView):
    model = NewsLetter
    paginate_by = 10
    template_name = "singlenews.html"

    def get_object(self):
        slug = self.kwargs.get("slug")  # Get slug from URL parameters
        if slug:
            return get_object_or_404(NewsLetter, slug=slug)  # Retrieve profile or raise 404 for invalid slug
        return None  # Handle case where no slug is provided (optional

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['News'] = NewsLetter.objects.all()

        newprofile = NewsLetter.objects.filter(is_active=1)
        # Retrieve the author's profile avatar

        context['Profiles'] = newprofile

        for newprofile in context['Profiles']:
            user = newprofile.user
            profile = Profile.objects.filter(user=user).first()
            if profile:
                newprofile.newprofile_profile_picture_url = profile.avatar.url
                newprofile.newprofile_profile_url = newprofile.get_profile_url()

        return context


# views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages  # Correct import
from django.contrib.auth.models import User
from .models import FriendRequest
from .forms import FriendRequestForm  # Make sure you have this form


def send_friend_request(request):
    if request.method == "POST":
        form = FriendRequestForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            receiver = get_object_or_404(User, username=username)

            # Prevent sending a friend request to oneself
            if receiver == request.user:
                messages.error(request, "You cannot send a friend request to yourself.")
                return redirect('send_friend_request')  # Redirect to the same page

            # Check if a request already exists
            existing_request = FriendRequest.objects.filter(sender=request.user, receiver=receiver).first()

            if existing_request:
                messages.error(request, "You have already sent a friend request to this user!")
            else:
                FriendRequest.objects.create(sender=request.user, receiver=receiver)
                messages.success(request, "Friend request sent successfully!")

            return redirect('send_friend_request')  # Redirect after processing

    else:
        form = FriendRequestForm()

    return render(request, 'send_friend_request.html', {'form': form})


def manage_friend_request(request, request_id, action):
    # Get the friend request object
    friend_request = get_object_or_404(FriendRequest, id=request_id)

    # Ensure the current user is either the sender or receiver of the request
    if request.user != friend_request.receiver:
        messages.error(request, "You are not authorized to manage this friend request.")
        return redirect('index')  # Redirect to an appropriate view

    # Process the action
    if action == 'accept':
        friend_request.status = FriendRequest.ACCEPTED
        friend_request.save()
        messages.success(request, f"You have accepted the friend request from {friend_request.sender.username}.")

    elif action == 'decline':
        friend_request.status = FriendRequest.DECLINED
        friend_request.save()
        messages.success(request, f"You have declined the friend request from {friend_request.sender.username}.")

    else:
        messages.info(request, "No action taken on the friend request.")

    # Redirect to the friend requests list or another relevant page
    return redirect(reverse('friend_requests_list'))  # Replace with your actual view name

class InternProfileCreateView(CreateView):
    model = InternProfile
    form_class = InternProfileForm
    template_name = 'intern_profile_form.html'
    success_url = reverse_lazy('intern_profile_success')  # Redirect after successful form submission

    def form_valid(self, form):
        # Set the user field to the currently logged-in user
        form.instance.user = self.request.user
        return super().form_valid(form)