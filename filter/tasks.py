## filter/tasks.py


from io import BytesIO
from os.path import basename
from celery import shared_task
from PIL import Image, ExifTags
from django.core.files.base import ContentFile
import logging
from .models import UploadedImage
from .linear_filter import find_shift, add_filter, get_field_view
import numpy as np

logger = logging.getLogger(__name__)

MAX_IMG_SIZE = 1440


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
        width, height = img.size

        if width > MAX_IMG_SIZE or height > MAX_IMG_SIZE:
            img.thumbnail((MAX_IMG_SIZE, MAX_IMG_SIZE), Image.Resampling.LANCZOS)
        downscaled_img = img

    except Image.UnidentifiedImageError as e:
        logger.error(f"Cannot identify image file: {e}")
        return None


    hor, ver = find_shift(float(image_instance.va), float(image_instance.cs))
    # print(f"Applying filter with va: {image_instance.va}, cs: {image_instance.cs}")
    # print(f"Applying filter with hor: {hor}, ver: {ver}")

    downscaled_filtered_img = add_filter(np.array(downscaled_img, dtype=np.uint8),
                                         1 / hor,
                                         ver,
                                         image_instance.camera,
                                         float(image_instance.sensor_h),
                                         float(image_instance.sensor_w),
                                         float(image_instance.focal_len))

    upscaled_filtered_img = downscaled_filtered_img
    img_out = Image.fromarray(upscaled_filtered_img)
    # img_out = Image.fromarray(np.array(downscaled_img)) # TODO: DELETE

    upscaled_filtered_img = Image.fromarray(downscaled_filtered_img).resize((width, height), Image.Resampling.LANCZOS)
    img_out = upscaled_filtered_img

    img_io = BytesIO()
    img_out.save(img_io, format='JPEG')

    original_name = basename(image_instance.image.name)
    base, _ = original_name.rsplit('.', 1)  # strip original extension

    image_instance.filtered_image.save(
        f"filtered_{base}.jpg",
        ContentFile(img_io.getvalue()),
        save=True
    )

    image_instance.status = 'Filtered'
    image_instance.save()
