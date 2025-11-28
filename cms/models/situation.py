from django.db import models


class Situation(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    glosses = models.ManyToManyField("Gloss", related_name="relevant_in_situations", blank=True)
    descriptions = models.ManyToManyField("Gloss", related_name="describes_situations", blank=True)

    image_link = models.URLField(blank=True, null=True)

    # use description gloss of language with iso "eng", if not exist, id
    def __str__(self):
        english_description = self.descriptions.filter(language__iso="eng").first()
        return english_description.content if english_description else self.id
