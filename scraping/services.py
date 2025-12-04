import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from .models import ScrapingJob, ScrapedData
import logging

logger = logging.getLogger(__name__)

class ScrapingService:
    @staticmethod
    def create_job(url):
        """Cria um novo job de scraping."""
        return ScrapingJob.objects.create(url=url)

    @staticmethod
    def execute_job(job_id):
        """Executa o job de scraping."""
        try:
            job = ScrapingJob.objects.get(id=job_id)
            job.status = 'running'
            job.started_at = timezone.now()
            job.save()

            # Faz a requisição HTTP
            response = requests.get(job.url, verify=False)
            response.raise_for_status()

            # Parse do HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extrai dados básicos
            title = soup.title.string if soup.title else None
            content = soup.get_text()

            # Cria o registro dos dados extraídos
            ScrapedData.objects.create(
                job=job,
                title=title,
                content=content,
                metadata={
                    'status_code': response.status_code,
                    'content_type': response.headers.get('content-type'),
                    'url': job.url
                }
            )

            # Atualiza o status do job
            job.status = 'completed'
            job.completed_at = timezone.now()
            job.save()

            return True

        except Exception as e:
            logger.error(f"Erro ao executar scraping job {job_id}: {str(e)}")
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = timezone.now()
            job.save()
            return False

    @staticmethod
    def get_job_status(job_id):
        """Retorna o status de um job."""
        try:
            job = ScrapingJob.objects.get(id=job_id)
            return {
                'id': job.id,
                'url': job.url,
                'status': job.status,
                'created_at': job.created_at,
                'started_at': job.started_at,
                'completed_at': job.completed_at,
                'error_message': job.error_message
            }
        except ScrapingJob.DoesNotExist:
            return None

    @staticmethod
    def get_scraped_data(job_id):
        """Retorna os dados extraídos de um job."""
        try:
            job = ScrapingJob.objects.get(id=job_id)
            data = ScrapedData.objects.filter(job=job).first()
            if data:
                return {
                    'title': data.title,
                    'content': data.content,
                    'metadata': data.metadata,
                    'created_at': data.created_at
                }
            return None
        except ScrapingJob.DoesNotExist:
            return None 