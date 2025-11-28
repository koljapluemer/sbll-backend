from django.db import models


class SpecificSituation(models.Model):
    id = models.CharField(max_length=64, primary_key=True)

    descriptions = models.ManyToManyField("Gloss", related_name="describes_specific_situations", blank=True)
    glosses = models.ManyToManyField("Gloss", related_name="relevant_in_specific_situations", blank=True)

    image_link = models.URLField(blank=True, null=True)

    target_language = models.ForeignKey("Language", related_name="target_specific_situations", on_delete=models.CASCADE)
    native_language = models.ForeignKey("Language", related_name="native_specific_situations", on_delete=models.CASCADE)

    # use description gloss of language with iso "eng", if not exist, id
    def __str__(self):
        english_description = self.descriptions.filter(language__iso="eng").first()
        return english_description.content if english_description else self.id
