from __future__ import annotations

import logging

import requests
from bs4 import BeautifulSoup
from django.utils import timezone

from .models import ScrapedData, ScrapingJob

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT_SECONDS: int = 30


class ScrapingService:
    """Serviço responsável pelo ciclo de vida de jobs de scraping."""

    @staticmethod
    def create_job(url: str) -> ScrapingJob:
        return ScrapingJob.objects.create(url=url)

    @staticmethod
    def execute_job(job_id: int) -> bool:
        """Executa o scraping de um job. Retorna True em sucesso, False em falha."""
        try:
            job = ScrapingJob.objects.get(id=job_id)
        except ScrapingJob.DoesNotExist:
            logger.error("Job %s não encontrado.", job_id)
            return False

        job.status = "running"
        job.started_at = timezone.now()
        job.save(update_fields=["status", "started_at"])

        try:
            response = requests.get(job.url, timeout=_REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string if soup.title else None
            content = soup.get_text()

            ScrapedData.objects.create(
                job=job,
                title=title,
                content=content,
                metadata={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type"),
                    "url": job.url,
                },
            )

            job.status = "completed"
            job.completed_at = timezone.now()
            job.save(update_fields=["status", "completed_at"])
            return True

        except Exception as exc:
            logger.exception("Erro ao executar scraping job %s", job_id)
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = timezone.now()
            job.save(update_fields=["status", "error_message", "completed_at"])
            return False

    @staticmethod
    def get_job_status(job_id: int) -> dict | None:
        try:
            job = ScrapingJob.objects.get(id=job_id)
        except ScrapingJob.DoesNotExist:
            return None

        return {
            "id": job.id,
            "url": job.url,
            "status": job.status,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "error_message": job.error_message,
        }

    @staticmethod
    def get_scraped_data(job_id: int) -> dict | None:
        try:
            job = ScrapingJob.objects.get(id=job_id)
        except ScrapingJob.DoesNotExist:
            return None

        data = ScrapedData.objects.filter(job=job).first()
        if not data:
            return None

        return {
            "title": data.title,
            "content": data.content,
            "metadata": data.metadata,
            "created_at": data.created_at,
        }
