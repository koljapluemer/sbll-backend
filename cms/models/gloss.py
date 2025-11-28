from django.db import models


class Gloss(models.Model):
    content = models.TextField()
    language = models.ForeignKey("Language", on_delete=models.CASCADE)
    transcriptions = models.JSONField(default=list)

    contains = models.ManyToManyField("self", related_name="contained_by", symmetrical=False, blank=True)
    near_synonyms = models.ManyToManyField("self", symmetrical=True, blank=True)
    near_homophones = models.ManyToManyField("self", symmetrical=True, blank=True)
    translations = models.ManyToManyField("self", symmetrical=True, blank=True)
    clarifies_usage = models.ManyToManyField("self", related_name="usage_of_clarified", symmetrical=False, blank=True)
    to_be_differentiated_from = models.ManyToManyField("self", symmetrical=True, blank=True)
    collocations = models.ManyToManyField("self", symmetrical=True, blank=True)

    # content+language should be unique together
    class Meta:
        unique_together = ("content", "language")

    def __str__(self):
        return f"{self.language}: {self.content}"

    def get_compound_key(self):
        """
        Returns a compound key for cross-referencing glosses without using internal IDs.
        Format: "{language_iso}:{content}"
        Example: "en:hello", "de:hallo"
        """
        return f"{self.language.iso}:{self.content}"

    def is_paraphrased(self):
        """
        Checks if this gloss is a paraphrased gloss.
        Paraphrased glosses have content wrapped in square brackets.
        Example: "[to say hello]"
        """
        return self.content.startswith("[") and self.content.endswith("]")
