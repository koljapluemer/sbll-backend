from django.db import models


class AIInteraction(models.Model):
    feature = models.CharField(max_length=100)
    input_data = models.JSONField()
    logging_data = models.JSONField()
    output_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.feature} - {self.created_at}"
