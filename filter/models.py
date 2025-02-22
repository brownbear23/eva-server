## filter/models.py


from django.db import models
class UploadedImage(models.Model):
    va = models.DecimalField(max_digits=10, decimal_places=2)
    cs = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='uploads/')
    filtered_image = models.ImageField(upload_to='filtered/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')

    def __str__(self):
        return self.image.name
