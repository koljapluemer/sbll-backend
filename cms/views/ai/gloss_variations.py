from django.http import JsonResponse
from django.views.decorators.http import require_POST
from cms.models import Gloss
from cms.ai.features.gloss_variations import generate_variations
import json


@require_POST
def generate_gloss_variations(request):
    """API endpoint to generate variations of a gloss"""
    try:
        data = json.loads(request.body)
        gloss_id = data.get("gloss_id")
        num_variations = data.get("num_variations", 3)

        if not gloss_id:
            return JsonResponse({"error": "gloss_id is required"}, status=400)

        try:
            gloss = Gloss.objects.get(id=gloss_id)
        except Gloss.DoesNotExist:
            return JsonResponse({"error": "Gloss not found"}, status=404)

        result = generate_variations(gloss.content, num_variations)

        return JsonResponse({
            "variations": result["variations"],
            "interaction_id": result["interaction_id"],
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
