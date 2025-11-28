from django.db import models


class Situation(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    glosses = models.ManyToManyField("Gloss", related_name="relevant_in_situations", blank=True)

    def __str__(self):
        return self.id
