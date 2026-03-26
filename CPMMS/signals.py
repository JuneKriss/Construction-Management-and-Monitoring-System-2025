from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *

@receiver(post_save, sender=Account)
def create_worker_for_account(sender, instance, created, **kwargs):
    if created and instance.role == 'worker':
        worker = Worker.objects.create(
            account_id=instance,
            first_name="Not Provided",
            last_name="Not Provided",
            age=25,
            gender='Not specified',
            contact='000-000-0000',
            address='Unknown Address',
            qr_code_text=str(instance.pk)
        )
        
        worker.save()
        
@receiver(post_save, sender=Account)
def create_personnel_for_account(sender, instance, created, **kwargs):
    if created and instance.role not in ['worker', 'admin']: 
        Personnel.objects.create(
            account_id=instance,
            first_name="Not Provided",  
            last_name="Not Provided",
            birthdate='1998-01-01', 
            gender='Not specified',
            contact='000-000-0000',
            address='Unknown Address',
            email='default@example.com',
        )
