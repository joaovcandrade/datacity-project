import requests
import json
import time

BASE_URL = 'http://localhost:8000/api/scraping'

def test_api():
    # 1. Criar um job
    print("1. Criando job de scraping...")
    response = requests.post(
        f'{BASE_URL}/jobs/',
        json={'url': 'https://www.gov.br/planalto/pt-br'}
    )
    print(f"Resposta: {response.status_code}")
    print(response.json())
    
    if response.status_code != 200:
        print("Erro ao criar job")
        return
    
    job_id = response.json()['id']
    
    # 2. Executar o job
    print("\n2. Executando job...")
    response = requests.post(f'{BASE_URL}/jobs/{job_id}/execute/')
    print(f"Resposta: {response.status_code}")
    print(response.json())
    
    # 3. Verificar status
    print("\n3. Verificando status...")
    time.sleep(2)  # Espera um pouco para o scraping terminar
    response = requests.get(f'{BASE_URL}/jobs/{job_id}/status/')
    print(f"Resposta: {response.status_code}")
    print(response.json())
    
    # 4. Obter dados
    print("\n4. Obtendo dados...")
    response = requests.get(f'{BASE_URL}/jobs/{job_id}/data/')
    print(f"Resposta: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

if __name__ == '__main__':
    test_api() 