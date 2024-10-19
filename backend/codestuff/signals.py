from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile, Subscription


@receiver(post_save, sender=Profile)
def create_or_update_subscription(sender, instance, created, **kwargs):
    # Check if a subscription already exists for this user
    subscription, created = Subscription.objects.get_or_create(
        user=instance.user,
        defaults={
            'email': instance.email,
            'profile': instance,
            'opt_in': instance.opt_in,
        }
    )

    # If the subscription already exists, update the fields
    if not created:
        subscription.email = instance.email
        subscription.profile = instance  # Although this may not need to change
        subscription.opt_in = instance.opt_in
        subscription.save()
