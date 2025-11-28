from django.db import models

class Gloss(models.Model):
    content = models.TextField()
    language = models.ForeignKeyField("Language")
    transcriptions = models.JSONField(default=list)

    contains = models.ManyToManyField("self", related_name="contained_by", symmetrical=False, blank=True)
    near_synonyms = models.ManyToManyField("self", symmetrical=True, blank=True)
    near_homophones = models.ManyToManyField("self", symmetrical=True, blank=True)
    translations = models.ManyToManyField("self", symmetrical=True, blank=True)
    clarifies_usage = models.ManyToManyField("self", related_name="usage_of_clarified", symmetrical=False, blank=True)
    to_be_differentiated_from = models.ManyToManyField("self", symmetrical=True, blank=True)
    collocations = models.ManyToManyField("self", symmetrical=True, blank=True)

    # content+language should be unique together