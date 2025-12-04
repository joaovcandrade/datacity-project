from django.core.management.base import BaseCommand
from accounts.models import Norm

class Command(BaseCommand):
    help = 'Corrige URLs de normas que não possuem protocolo'

    def handle(self, *args, **kwargs):
        norms = Norm.objects.all()
        updated_count = 0

        for norm in norms:
            url = norm.Direcionamento
            if url and not url.startswith(('http://', 'https://')):
                norm.Direcionamento = 'https://' + url
                norm.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'URL corrigida para {norm.Nome}: {norm.Direcionamento}')
                )

        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n{updated_count} norma(s) corrigida(s) com sucesso!')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Todas as normas já possuem URLs válidas.')
            )