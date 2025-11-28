from django.db import models

class Note(models.Model):
    gloss = models.ForeignKey(Gloss)
    note_type = models.CharField(max_length=64)
    content = models.TextField()
    show_before_solution = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.note_type}: {self.content}"
