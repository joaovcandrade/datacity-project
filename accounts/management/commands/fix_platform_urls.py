from django.core.management.base import BaseCommand
from accounts.models import Platform

class Command(BaseCommand):
    help = 'Corrige URLs de plataformas que não possuem protocolo'

    def handle(self, *args, **kwargs):
        platforms = Platform.objects.all()
        updated_count = 0

        for platform in platforms:
            url = platform.Direcionamento
            if url and not url.startswith(('http://', 'https://')):
                platform.Direcionamento = 'https://' + url
                platform.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'URL corrigida para {platform.Nome}: {platform.Direcionamento}')
                )

        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n{updated_count} plataforma(s) corrigida(s) com sucesso!')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Todas as plataformas já possuem URLs válidas.')
            )