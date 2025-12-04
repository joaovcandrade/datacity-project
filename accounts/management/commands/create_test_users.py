from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

class Command(BaseCommand):
    help = 'Cria usuários de teste com diferentes níveis de acesso'

    def handle(self, *args, **kwargs):
        # Lista de usuários para criar
        users = [
            {
                'username': 'admin',
                'email': 'admin@datacity.com',
                'password': 'admin123',
                'user_type': 'ADMIN',
                'is_staff': True,
                'is_superuser': True
            },
            {
                'username': 'gestor',
                'email': 'gestor@datacity.com',
                'password': 'gestor123',
                'user_type': 'MANAGER',
                'is_staff': True,
                'is_superuser': False
            },
            {
                'username': 'usuario',
                'email': 'usuario@datacity.com',
                'password': 'usuario123',
                'user_type': 'COMMON',
                'is_staff': False,
                'is_superuser': False
            }
        ]

        for user_data in users:
            try:
                # Verifica se o usuário já existe
                if User.objects.filter(username=user_data['username']).exists():
                    self.stdout.write(
                        self.style.WARNING(f'Usuário {user_data["username"]} já existe')
                    )
                    continue

                # Cria o usuário
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    user_type=user_data['user_type'],
                    is_staff=user_data['is_staff'],
                    is_superuser=user_data['is_superuser']
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Usuário {user_data["username"]} criado com sucesso! '
                        f'Tipo: {user_data["user_type"]}'
                    )
                )

            except IntegrityError as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Erro ao criar usuário {user_data["username"]}: {str(e)}'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Erro inesperado ao criar usuário {user_data["username"]}: {str(e)}'
                    )
                )

        self.stdout.write(self.style.SUCCESS('\nProcesso de criação de usuários concluído!')) 