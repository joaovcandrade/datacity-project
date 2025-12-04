from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PowerBIScraper:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = None
        
    def setup_driver(self):
        chrome_options = Options()
        
        # Opções para evitar detecção de bot
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Outras opções úteis
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        # chrome_options.add_argument('--headless')  # Descomente se necessário
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Remove a propriedade webdriver
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def wait_and_find_element(self, by, value, timeout=20):
        """Método auxiliar para aguardar e encontrar elementos"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            logger.error(f"Elemento não encontrado: {by}={value}, Erro: {e}")
            return None
    
    def login(self):
        logger.info("Iniciando processo de login no Power BI...")
        
        try:
            self.driver.get("https://app.powerbi.com")
            time.sleep(3)
            
            # Múltiplas estratégias para encontrar o botão de login
            login_selectors = [
                "button[data-testid='sign-in-button']",
                "a[href*='login']",
                "button:contains('Sign in')",
                ".sign-in-button",
                "#sign-in-button",
                "button[aria-label*='Sign in']"
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    login_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"Botão de login encontrado com seletor: {selector}")
                    break
                except:
                    continue
            
            if not login_button:
                logger.error("Nenhum botão de login encontrado. Tentando navegação direta...")
                self.driver.get("https://login.microsoftonline.com/")
                time.sleep(3)
            else:
                login_button.click()
                time.sleep(3)
            
            # Aguardar carregamento da página de login
            self.handle_login_form()
            
        except Exception as e:
            logger.error(f"Erro no processo de login: {e}")
            self.save_debug_info()
            raise
    
    def handle_login_form(self):
        """Lida com o formulário de login da Microsoft"""
        logger.info("Processando formulário de login...")
        
        # Possíveis seletores para o campo de email
        email_selectors = [
            "input[type='email']",
            "input[name='loginfmt']",
            "#i0116",
            "input[placeholder*='email']",
            "input[placeholder*='Email']"
        ]
        
        email_input = None
        for selector in email_selectors:
            email_input = self.wait_and_find_element(By.CSS_SELECTOR, selector, 5)
            if email_input:
                logger.info(f"Campo de email encontrado: {selector}")
                break
        
        if not email_input:
            raise Exception("Campo de email não encontrado")
        
        # Inserir email
        email_input.clear()
        email_input.send_keys(self.email)
        
        # Procurar botão "Próximo" ou submit
        next_selectors = [
            "input[type='submit']",
            "button[type='submit']",
            "#idSIButton9",
            "input[value='Next']",
            "button:contains('Next')"
        ]
        
        next_button = None
        for selector in next_selectors:
            try:
                next_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                break
            except:
                continue
        
        if next_button:
            next_button.click()
        else:
            # Tentar submit no formulário
            email_input.submit()
        
        time.sleep(3)
        
        # Inserir senha
        self.handle_password_form()
    
    def handle_password_form(self):
        """Lida com o campo de senha"""
        logger.info("Inserindo senha...")
        
        password_selectors = [
            "input[type='password']",
            "input[name='passwd']",
            "#i0118",
            "input[placeholder*='password']",
            "input[placeholder*='Password']"
        ]
        
        password_input = None
        for selector in password_selectors:
            password_input = self.wait_and_find_element(By.CSS_SELECTOR, selector, 10)
            if password_input:
                logger.info(f"Campo de senha encontrado: {selector}")
                break
        
        if not password_input:
            raise Exception("Campo de senha não encontrado")
        
        password_input.clear()
        password_input.send_keys(self.password)
        
        # Botão de login
        login_selectors = [
            "input[type='submit']",
            "button[type='submit']",
            "#idSIButton9",
            "input[value='Sign in']"
        ]
        
        login_button = None
        for selector in login_selectors:
            try:
                login_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                break
            except:
                continue
        
        if login_button:
            login_button.click()
        else:
            password_input.submit()
        
        time.sleep(5)
        
        # Lidar com "Manter conectado?"
        self.handle_stay_signed_in()
    
    def handle_stay_signed_in(self):
        """Lida com a pergunta 'Manter conectado?'"""
        try:
            # Procurar botão "Não"
            no_selectors = [
                "#idBtn_Back",
                "button:contains('No')",
                "input[value='No']",
                "button[data-report-event='Signin_No_Stay_Signed_In_Click']"
            ]
            
            for selector in no_selectors:
                try:
                    no_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    no_button.click()
                    logger.info("Clicou em 'Não' para manter conectado")
                    break
                except:
                    continue
        except:
            logger.info("Pergunta 'Manter conectado?' não apareceu ou já foi processada")
        
        time.sleep(3)
    
    def access_report(self, report_url):
        logger.info(f"Acessando relatório: {report_url}")
        self.driver.get(report_url)
        
        # Aguardar carregamento do relatório
        self.wait_for_report_load()
        
    def wait_for_report_load(self):
        """Aguarda o relatório carregar completamente"""
        logger.info("Aguardando carregamento do relatório...")
        
        # Aguardar elementos específicos do Power BI
        report_selectors = [
            ".visual-container",
            ".explorationContainer",
            "[data-testid='visual-container']",
            ".chart-container"
        ]
        
        for selector in report_selectors:
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                logger.info(f"Relatório carregado - elemento encontrado: {selector}")
                break
            except:
                continue
        
        # Aguardar adicional para garantir carregamento completo
        time.sleep(10)
    
    def extract_data(self):
        logger.info("Extraindo dados do relatório...")
        
        data = {
            'title': self.driver.title,
            'url': self.driver.current_url,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'visuals': [],
            'tables': [],
            'texts': []
        }
        
        try:
            # Extrair dados visuais
            visual_containers = self.driver.find_elements(By.CSS_SELECTOR, ".visual-container")
            logger.info(f"Encontrados {len(visual_containers)} containers visuais")
            
            for i, container in enumerate(visual_containers):
                try:
                    # Extrair texto do container
                    container_text = container.text
                    if container_text:
                        data['texts'].append({
                            'type': 'visual',
                            'index': i,
                            'text': container_text
                        })
                    
                    # Extrair dados da tabela se existir
                    tables = container.find_elements(By.CSS_SELECTOR, "table")
                    for table in tables:
                        try:
                            rows = table.find_elements(By.TAG_NAME, "tr")
                            table_data = []
                            for row in rows:
                                cells = row.find_elements(By.TAG_NAME, "td")
                                if not cells:  # Se não encontrar td, tenta th
                                    cells = row.find_elements(By.TAG_NAME, "th")
                                row_data = [cell.text for cell in cells]
                                if row_data:  # Só adiciona se houver dados
                                    table_data.append(row_data)
                            
                            if table_data:  # Só adiciona se a tabela tiver dados
                                data['tables'].append({
                                    'visual_index': i,
                                    'data': table_data
                                })
                        except Exception as e:
                            logger.warning(f"Erro ao extrair tabela do visual {i}: {e}")
                    
                    # Extrair dados do visual
                    visual_data = {
                        'index': i,
                        'text': container_text,
                        'html': container.get_attribute('innerHTML')[:1000]  # Limitar HTML
                    }
                    data['visuals'].append(visual_data)
                    
                except Exception as e:
                    logger.warning(f"Erro ao extrair dados do visual {i}: {e}")
            
            # Extrair textos adicionais da página
            text_elements = self.driver.find_elements(By.CSS_SELECTOR, "p, h1, h2, h3, h4, h5, h6, span, div")
            for element in text_elements:
                try:
                    text = element.text.strip()
                    if text and len(text) > 1:  # Ignorar textos muito curtos
                        data['texts'].append({
                            'type': 'text',
                            'tag': element.tag_name,
                            'text': text
                        })
                except:
                    continue
            
            logger.info(f"Extraídos {len(data['visuals'])} visuais, {len(data['tables'])} tabelas e {len(data['texts'])} textos")
            
        except Exception as e:
            logger.error(f"Erro na extração de dados: {e}")
            self.save_debug_info()
        
        return data
    
    def save_debug_info(self):
        """Salva informações de debug em caso de erro"""
        try:
            debug_data = {
                'url': self.driver.current_url,
                'title': self.driver.title,
                'page_source': self.driver.page_source[:5000]  # Primeiros 5000 caracteres
            }
            
            with open('debug_powerbi.json', 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)
            
            # Salvar screenshot se possível
            self.driver.save_screenshot('debug_screenshot.png')
            logger.info("Informações de debug salvas em debug_powerbi.json e debug_screenshot.png")
        except Exception as e:
            logger.error(f"Erro ao salvar debug: {e}")
    
    def save_data(self, data, filename='powerbi_data.json'):
        logger.info(f"Salvando dados em {filename}...")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def close(self):
        if self.driver:
            self.driver.quit()

def main():
    # ATENÇÃO: Remova as credenciais reais antes de compartilhar o código
    EMAIL = "datacityapi@outlook.com"
    PASSWORD = "12345678910$&@"
    REPORT_URL = "https://app.powerbi.com/view?r=eyJrIjoiODhhNmI1ZWYtMmZmYy00NjVlLTk4MjQtYjlmMTUxZTJlYTI0IiwidCI6IjA0ZTcxZThlLTUwZDMtNDU1ZC04ODAzLWM3ZGI4ODhkNjRiYiJ9"
    
    scraper = PowerBIScraper(EMAIL, PASSWORD)
    
    try:
        scraper.setup_driver()
        scraper.login()
        scraper.access_report(REPORT_URL)
        data = scraper.extract_data()
        scraper.save_data(data)
        logger.info("Scraping concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante o scraping: {e}")
        scraper.save_debug_info()
        
    finally:
        scraper.close()

if __name__ == "__main__":
    main()