class SpecificSituation(models.Model):
    id = models.CharField(max_length=64, primary_key=True)

    descriptions = models.ManyToManyField("Gloss", related_name="describes_specific_situations", blank=True)
    glosses = models.ManyToManyField("Gloss", related_name="relevant_in_specific_situations", blank=True)

    image_link = models.URLField(blank=True, null=True)

    target_language = models.ForeignKeyField("Language")
    native_language = models.ForeignKeyField("Language")

    # use description gloss of language with iso "eng", if not exist, id
    def __str__(self):
        return self.id