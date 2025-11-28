from django.db import models


class Language(models.Model):
    iso = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=128)
    short = models.CharField(max_length=50, null=True, blank=True)

    ai_note = models.TextField(blank=True)

    # add print function using short when available, otherwise name
    def __str__(self):
        return self.short or self.name
