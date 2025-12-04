import os
import django
import psycopg2
from psycopg2 import OperationalError
from django.conf import settings

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datacity.settings')
django.setup()

def test_postgres_connection():
    """Testa a conexão direta com o PostgreSQL"""
    try:
        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )
        print("✅ Conexão direta com PostgreSQL bem-sucedida!")
        
        # Testar a criação de uma tabela temporária
        cur = conn.cursor()
        cur.execute("""
            CREATE TEMPORARY TABLE test_connection (
                id serial PRIMARY KEY,
                test_field varchar(50)
            )
        """)
        print("✅ Criação de tabela temporária bem-sucedida!")
        
        # Testar inserção de dados
        cur.execute("""
            INSERT INTO test_connection (test_field)
            VALUES ('teste de conexão')
        """)
        print("✅ Inserção de dados bem-sucedida!")
        
        # Testar consulta
        cur.execute("SELECT * FROM test_connection")
        result = cur.fetchone()
        print(f"✅ Consulta bem-sucedida! Dados recuperados: {result}")
        
        # Limpar
        cur.close()
        conn.close()
        print("✅ Conexão fechada com sucesso!")
        
    except OperationalError as e:
        print(f"❌ Erro ao conectar ao PostgreSQL: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

def test_django_connection():
    """Testa a conexão através do Django"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print("✅ Conexão Django com o banco de dados bem-sucedida!")
            print(f"✅ Resultado do teste: {result}")
    except Exception as e:
        print(f"❌ Erro na conexão Django: {e}")

if __name__ == "__main__":
    print("\n=== Testando conexão direta com PostgreSQL ===")
    test_postgres_connection()
    
    print("\n=== Testando conexão através do Django ===")
    test_django_connection() 