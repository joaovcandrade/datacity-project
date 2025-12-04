import os
import django
from django.db import connections
from django.db.utils import OperationalError

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datacity.settings')
django.setup()

def migrate_data():
    try:
        # Testar conexão com PostgreSQL
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT 1")
            print("Conexão com PostgreSQL estabelecida com sucesso!")
    except OperationalError:
        print("Erro ao conectar com PostgreSQL. Verifique se:")
        print("1. O PostgreSQL está instalado e rodando")
        print("2. O banco de dados 'datacity' existe")
        print("3. O usuário 'postgres' tem a senha 'postgres'")
        print("4. O PostgreSQL está rodando na porta 5432")
        return

    # Criar o banco de dados se não existir
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("CREATE DATABASE datacity")
            print("Banco de dados 'datacity' criado com sucesso!")
    except Exception as e:
        print(f"Banco de dados já existe ou erro ao criar: {e}")

    # Aplicar migrações
    os.system('python manage.py migrate')

    # Criar usuários de teste
    os.system('python manage.py create_test_users')

    print("\nMigração concluída com sucesso!")
    print("Você pode agora remover o arquivo db.sqlite3")

if __name__ == '__main__':
    migrate_data() 