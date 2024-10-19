from django.contrib import admin

from .models import Major, Keywords, PersonalProfile, Profile, InternProfile, Room, NewsLetter, Subscription, \
    LandingImage, Community, Message, Friend, FriendRequest, Notification

admin.site.register(Major)
admin.site.register(Keywords)
admin.site.register(PersonalProfile)
admin.site.register(Profile)
admin.site.register(InternProfile)
admin.site.register(NewsLetter)
admin.site.register(Subscription)
admin.site.register(Message)
admin.site.register(Friend)
admin.site.register(Notification)
admin.site.register(FriendRequest)
admin.site.register(LandingImage)
admin.site.register(Room)

from django.contrib import admin
from .models import Community, Role, CommunityRoleAssignment, Room

class RoleInline(admin.TabularInline):
    model = Role
    extra = 1  # Number of empty rows to display

class RoomInline(admin.TabularInline):
    model = Room
    extra = 1  # Number of empty rows to display

class CommunityRoleAssignmentInline(admin.TabularInline):
    model = CommunityRoleAssignment
    extra = 1  # Number of empty rows to display

@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'owner', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [RoleInline, RoomInline, CommunityRoleAssignmentInline]
