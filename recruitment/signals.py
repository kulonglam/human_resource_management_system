from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Application, JobPosting
from .services import ensure_default_pipeline_stages, initial_stage_for_job


@receiver(post_save, sender=JobPosting)
def create_default_pipeline(sender, instance, created, **kwargs):
    if created:
        ensure_default_pipeline_stages(instance)


@receiver(post_save, sender=Application)
def set_initial_pipeline_stage(sender, instance, created, **kwargs):
    if created and not instance.current_stage_id:
        stage = initial_stage_for_job(instance.job)
        if stage:
            instance.current_stage = stage
            Application.objects.filter(pk=instance.pk).update(current_stage=stage)
