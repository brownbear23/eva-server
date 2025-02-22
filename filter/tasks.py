## filter/tasks.py


from io import BytesIO
from os.path import basename

from celery import shared_task
from PIL import Image
from django.core.files.base import ContentFile
import logging
from .models import UploadedImage
from .linear_filter import find_shift, add_filter
import numpy as np

logger = logging.getLogger(__name__)

@shared_task
def process_image(uploaded_image_id):
    image_instance = UploadedImage.objects.get(id=uploaded_image_id)

    image_instance.image.open()

    img_bytes = image_instance.image.read()

    if not img_bytes:
        logger.error("Image file is empty or could not be read")
        return None

    try:
        img = Image.open(BytesIO(img_bytes)).convert('RGB')
    except Image.UnidentifiedImageError as e:
        logger.error(f"Cannot identify image file: {e}")
        return None
    # logger.info(f"Applying filter with va: {image_instance.va}, cs: {image_instance.cs}")
    hor, ver = find_shift(float(image_instance.va), float(image_instance.cs))
    # logger.info(f"Applying filter with hor: {hor}, ver: {ver}")
    filtered_img = add_filter(np.array(img, dtype=np.uint8), 1/hor, ver, camera = True, white_balance=False)


    img_out = Image.fromarray(filtered_img)
    img_io = BytesIO()
    img_out.save(img_io, format='JPEG')


    image_instance.filtered_image.save(
        f"filtered_{basename(image_instance.image.name)}",
        ContentFile(img_io.getvalue()),
        save=True
    )

    image_instance.status = 'Filtered'
    image_instance.save()




