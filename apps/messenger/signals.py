from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from fcm_django.models import FCMDevice

from apps.messenger.models import UserInfo, DeviceInfo


@receiver(post_save, sender=get_user_model())
def create_user_info(sender, instance, created, **kwargs):
    if created:
        UserInfo.objects.create(user=instance)


@receiver(post_save, sender=DeviceInfo)
def update_device_token(sender, instance: DeviceInfo, **kwargs):
    token = None
    device_type = None
    if instance.gcm_id:
        token = instance.gcm_id
        device_type = 'android'
    elif instance.apn_id:
        token = instance.apn_id
        device_type = 'ios'
    elif instance.void_apn_id:
        token = instance.void_apn_id
        device_type = 'web'
    if token and device_type:
        device, _ = FCMDevice.objects.update_or_create(device_id=instance.id, user_id=instance.user_id)
        device.registration_id = token
        device.type = device_type
        device.save()
