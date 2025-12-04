from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .services import ScrapingService

# Create your views here.

@csrf_exempt
@require_http_methods(["POST"])
def create_scraping_job(request):
    """Cria um novo job de scraping."""
    try:
        data = json.loads(request.body)
        url = data.get('url')
        
        if not url:
            return JsonResponse({'error': 'URL é obrigatória'}, status=400)
        
        job = ScrapingService.create_job(url)
        return JsonResponse({
            'id': job.id,
            'url': job.url,
            'status': job.status,
            'created_at': job.created_at
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_job_status(request, job_id):
    """Retorna o status de um job."""
    status = ScrapingService.get_job_status(job_id)
    if status:
        return JsonResponse(status)
    return JsonResponse({'error': 'Job não encontrado'}, status=404)

@require_http_methods(["GET"])
def get_scraped_data(request, job_id):
    """Retorna os dados extraídos de um job."""
    data = ScrapingService.get_scraped_data(job_id)
    if data:
        return JsonResponse(data)
    return JsonResponse({'error': 'Dados não encontrados'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
def execute_job(request, job_id):
    """Executa um job de scraping."""
    success = ScrapingService.execute_job(job_id)
    if success:
        return JsonResponse({'message': 'Job executado com sucesso'})
    return JsonResponse({'error': 'Erro ao executar job'}, status=500)
