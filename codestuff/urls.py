from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetCompleteView, \
    PasswordResetDoneView
from django.urls import path, path, include

from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.conf.urls.i18n import i18n_patterns


from . import views
from .views import UserCommunitiesView, ProfileCreateView, PersonalProfileCreateView, InternProfileCreateView, \
    ProfileView

urlpatterns = [
    path('', views.LandingImageView.as_view(), name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('create_community/', views.CreateCommunityView.as_view(), name='create_community'),
    path('user_communities/', UserCommunitiesView.as_view(), name='user_communities'),
    path('friendslist/', views.FriendView.as_view(), name='friendslist'),
    path('friendslist_results/', views.FriendView.as_view(), name='friendslistresults'),
    path('friend-search/', views.FriendSearchResultsView.as_view(), name='friend-search'),
    path('friendslist/search/', views.FriendSearchResultsView.as_view(), name='friend_search'),
    path('nav/', TemplateView.as_view(template_name='nav.html'), name='nav'),
    path('base/', TemplateView.as_view(template_name='base.html'), name='base'),
    path('signup_success/', views.signup_success, name='signup_success'),
    path('profile/<str:username>/', ProfileView.as_view(), name='profile'),
    path('create-intern-profile/', views.InternProfileCreateView.as_view(), name='create_intern_profile'),
    path('intern-profile-success/', views.TemplateView.as_view(template_name='intern_profile_success.html'), name='intern_profile_success'),
    path('profile/create/', ProfileCreateView.as_view(), name='create_profile'),
    path('personal-profile/create/', PersonalProfileCreateView.as_view(), name='create_personal_profile'),
    path('intern-profile/create/', InternProfileCreateView.as_view(), name='create_intern_profile'),
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('event_list/', views.EventView.as_view(), name='event_list'),
    path('community/join/<uuid:invite_token>/', views.join_community, name='community_invite'),
    path('community/', views.ChatView.as_view(), name='community'),
    path('community/<str:slug>/', views.CommunityView.as_view(), name='community_index'),
    path('community/<str:slug>/create-room/', views.CreateRoomView.as_view(), name='create_room'),
    path('community/<str:slug>/<str:room>/', views.RoomView.as_view(), name='room'),
    path('community/<str:slug>/<str:room>/messages/', views.getMessages, name='get_messages'),
    path('calls/generate_token/', views.generate_token, name='generate_token'),
    path('news_list/', views.NewsView.as_view(), name='news_list'),
    path('singlenews/<slug:slug>/', views.SingleNewsView.as_view(), name='singlenews'),
    path('send_friend_request/', views.send_friend_request, name='send_friend_request'),
    path('intern-profiles/', views.InternProfileCreateView.as_view(), name='intern_profiles_list'),
    path('intern-profile/<int:pk>/', views.intern_profile_detail, name='intern_profile_detail'),
    path('similar-profiles/', views.find_similar_profiles, name='similar-profiles'),
    path('soughtprofile/<int:pk>/', views.profile_detail, name='soughtprofile'),  # Optional detail view
    path('personal_profile_form/', views.PersonalProfileCreateView.as_view(), name='personal_profile_form'),  # Optional detail view


    path('friend_request/<int:request_id>/<str:action>/', views.manage_friend_request, name='manage_friend_request'),

    #path('direct_messages/<str:friend_username>/', views.get_or_create_direct_message, name='direct_messages'),
    # URL to create or retrieve a DirectMessage room and redirect to the chat page
    #path('direct_messages/create/<str:friend_username>/', views.get_or_create_direct_message, name='create_direct_message'),

    # URL to load the chat room (handled by DirectMessageView)
    #path('direct_messages/chat/<str:label>/', views.DirectMessageView.as_view(), name='chat_room'),

    path('community/<str:slug>/<str:room>/send', views.send, name='send'),
    #path('getDirectMessages/<str:room>/', views.getDirectMessages, name='getDirectMessages'),
    #path('send_post_to_friend/<int:post_id>/', views.send_post_to_friend, name='send_post_to_friend'),
    #path('send_post_to_friend/<int:post_id>/<str:room_name>/', views.send_post_to_friend, name='send_post_to_friend'),
    path('events/', views.EventView.as_view(), name="events"),
    path('about/', views.AboutView.as_view(), name='about'),
    path('supportemail/', views.SupportEmailView.as_view(), name='supportemail'),
    path('success/', views.ContactSuccessView.as_view(), name='success'),
    path('reset_password/', PasswordResetView.as_view(), name='reset_password'),
    path('reset-password/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset_password/confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset-password/complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='commons/password-reset/password_reset.html',
                                              subject_template_name='commons/password-reset/password_reset_subject.txt',
                                              email_template_name='commons/password-reset/password_reset_email.html',
                                              success_url='/login/'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='commons/password-reset/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='commons/password-reset/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='commons/password-reset/password_reset_complete.html'),
         name='password_reset_complete'),

    path('events/<int:event_id>/rsvp/', views.rsvp_event, name='rsvp_event'),

]
