# filter/views.py


from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import UploadedImage
from .tasks import process_image
from django.shortcuts import render
import decimal



ALLOWED_FILE_TYPES = ['image/jpeg', 'image/png']

def index(request):
    return render(request, 'filter_ui.html')

@csrf_exempt
def upload_image_api(request):
    """
    API endpoint to upload an image via POST, store VA/CS values, and start processing.
    """
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            va_value = decimal.Decimal(request.POST.get('va'))
            cs_value = decimal.Decimal(request.POST.get('cs'))
        except (TypeError, ValueError, decimal.InvalidOperation):
            return JsonResponse({'error': 'Invalid VA or CS values. Must be numeric.'}, status=400)

        # Save the uploaded image and VA/CS values into the model
        uploaded_image = UploadedImage.objects.create(
            image=request.FILES['image'],
            va=va_value,
            cs=cs_value
        )

        # Triggering Celery task to filter the image
        process_image.delay(uploaded_image.id)

        # Respond with image ID and initial status
        return JsonResponse({'id': uploaded_image.id, 'status': 'Processing'}, status=202)

    return JsonResponse({'error': 'Invalid request'}, status=400)


def check_status_api(request, image_id):
    """
    API endpoint to check the status of an uploaded image processing task.
    """
    # Retrieve the image record
    image_record = get_object_or_404(UploadedImage, id=image_id)

    # Prepare the response based on the current status
    response_data = {
        'id': image_record.id,
        'status': image_record.status,
    }

    if image_record.status == 'Filtered':
        response_data['filtered_image_url'] = image_record.filtered_image.url

    return JsonResponse(response_data, status=200)
