"""
Scraper de acoes da Mais Retorno usando Selenium.

Objetivo:
- Percorrer todas as paginas de https://maisretorno.com/lista-acoes/page/1
- Extrair Ticker, Nome e Setor
- Salvar o resultado em um CSV UTF-8 
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


BASE_URL = "https://maisretorno.com/lista-acoes/page/{page}"
ARQUIVO_SAIDA = "acoes_b3.csv"
HEADLESS = True
TIMEOUT = 20

# Estrutura-base informada pelo usuario.
XPATH_LISTA_ITENS = "/html/body/div[1]/main/ul"
XPATH_PAGINACAO = "/html/body/div[1]/main/nav/ul"

# Adaptados para uso relativo dentro de cada <li>, mantendo a mesma referencia estrutural.
XPATH_ITEM_TICKER = ".//div/div[1]/a/p"
XPATH_ITEM_NOME = ".//div/div[1]/p"
XPATH_ITEM_SETOR = ".//div/div[4]/p[2]"


def configurar_driver() -> webdriver.Chrome:
    """Cria e devolve uma instancia configurada do Chrome."""
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    if HEADLESS:
        options.add_argument("--headless=new")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(TIMEOUT)
    return driver


def esperar_documento_pronto(driver: webdriver.Chrome, timeout: int = TIMEOUT) -> None:
    """Espera o navegador terminar o carregamento do documento."""
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def obter_texto_seguro(elemento, xpath_relativo: str, campo: str) -> str:
    """Le um texto usando XPath relativo e devolve string vazia se falhar."""
    try:
        return elemento.find_element(By.XPATH, xpath_relativo).text.strip()
    except NoSuchElementException:
        print(f"  [aviso] Campo '{campo}' nao encontrado para um item.")
        return ""


def obter_pagina_do_titulo(driver: webdriver.Chrome) -> Optional[int]:
    """
    Extrai o numero da pagina atual a partir do H1.
    Exemplo esperado: 'Lista de acoes na bolsa de valores B3 (Pagina 1)'.
    """
    try:
        titulo = WebDriverWait(driver, TIMEOUT).until(
            EC.visibility_of_element_located((By.XPATH, "//main//h1"))
        )
        match = re.search(r"P.gina\s+(\d+)", titulo.text, re.IGNORECASE)
        return int(match.group(1)) if match else None
    except TimeoutException:
        return None


def carregar_pagina(driver: webdriver.Chrome, numero_pagina: int, pagina_anterior: Optional[int]) -> bool:
    """
    Abre uma pagina e valida se o conteudo carregado corresponde ao numero esperado.
    """
    url = BASE_URL.format(page=numero_pagina)
    print(f"\n[Abrindo] Pagina {numero_pagina}: {url}")

    try:
        driver.get(url)
        esperar_documento_pronto(driver)

        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, XPATH_LISTA_ITENS))
        )
        WebDriverWait(driver, TIMEOUT).until(
            lambda d: len(d.find_elements(By.XPATH, f"{XPATH_LISTA_ITENS}/li")) > 0
        )

        pagina_lida = obter_pagina_do_titulo(driver)
        if pagina_lida is None:
            print("  [erro] Nao foi possivel confirmar o numero da pagina pelo titulo.")
            return False

        if pagina_lida != numero_pagina:
            print(
                f"  [fim] A pagina carregada indica 'Pagina {pagina_lida}', "
                f"mas a esperada era 'Pagina {numero_pagina}'."
            )
            return False

        if pagina_anterior is not None and pagina_lida == pagina_anterior:
            print("  [fim] O site nao avancou para uma nova pagina.")
            return False

        print(f"  [ok] Pagina {pagina_lida} carregada corretamente.")
        return True

    except TimeoutException:
        print(f"  [erro] Timeout ao carregar a pagina {numero_pagina}.")
        return False
    except WebDriverException as exc:
        print(f"  [erro] Falha de navegador na pagina {numero_pagina}: {exc}")
        return False


def extrair_itens_da_pagina(driver: webdriver.Chrome) -> List[Dict[str, str]]:
    """
    Extrai Ticker, Nome e Setor de todos os <li> da pagina atual.
    """
    registros: List[Dict[str, str]] = []

    itens = WebDriverWait(driver, TIMEOUT).until(
        EC.presence_of_all_elements_located((By.XPATH, f"{XPATH_LISTA_ITENS}/li"))
    )

    for indice, item in enumerate(itens, start=1):
        try:
            ticker = obter_texto_seguro(item, XPATH_ITEM_TICKER, "Ticker")
            nome = obter_texto_seguro(item, XPATH_ITEM_NOME, "Nome")
            setor = obter_texto_seguro(item, XPATH_ITEM_SETOR, "Setor")

            if not ticker or not nome or not setor:
                print(f"  [aviso] Item {indice} ignorado por dados incompletos.")
                continue

            registros.append(
                {
                    "Ticker": ticker,
                    "Nome": nome,
                    "Setor": setor,
                }
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  [aviso] Erro ao processar item {indice}: {exc}")

    return registros


def existe_proxima_pagina(driver: webdriver.Chrome, pagina_atual: int) -> bool:
    """
    Verifica se a paginacao da pagina atual oferece um link para a proxima pagina.
    """
    proxima_pagina = pagina_atual + 1

    try:
        paginacao = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, XPATH_PAGINACAO))
        )
    except TimeoutException:
        print("  [fim] Paginacao nao encontrada; assumindo que esta e a ultima pagina.")
        return False

    links = paginacao.find_elements(By.XPATH, ".//a")
    if not links:
        print("  [fim] Nenhum link de paginacao encontrado.")
        return False

    paginas_numericas: List[int] = []

    for link in links:
        href = (link.get_attribute("href") or "").strip()
        texto = link.text.strip()

        if texto.isdigit():
            paginas_numericas.append(int(texto))

        if texto == str(proxima_pagina):
            return True

        if href.endswith(f"/page/{proxima_pagina}") or f"/page/{proxima_pagina}/" in href:
            return True

    if paginas_numericas and proxima_pagina <= max(paginas_numericas):
        return True

    print(f"  [fim] Nao ha link visivel para a pagina {proxima_pagina}.")
    return False


def salvar_csv(registros_por_ticker: Dict[str, Dict[str, str]], caminho_saida: Path) -> None:
    """Salva os dados em CSV UTF-8 com exatamente tres colunas."""
    with caminho_saida.open("w", newline="", encoding="utf-8") as arquivo_csv:
        writer = csv.DictWriter(arquivo_csv, fieldnames=["Ticker", "Nome", "Setor"])
        writer.writeheader()
        writer.writerows(registros_por_ticker.values())


def executar_scraping() -> None:
    """Funcao principal do scraping."""
    driver: Optional[webdriver.Chrome] = None
    registros_por_ticker: Dict[str, Dict[str, str]] = {}
    pagina_atual = 1
    pagina_anterior: Optional[int] = None
    saida = Path(ARQUIVO_SAIDA).resolve()

    try:
        driver = configurar_driver()
        print("[Inicio] Navegador iniciado com sucesso.")

        while True:
            carregou = carregar_pagina(driver, pagina_atual, pagina_anterior)
            if not carregou:
                break

            registros_pagina = extrair_itens_da_pagina(driver)
            print(f"  [info] Pagina {pagina_atual} retornou {len(registros_pagina)} registros validos.")

            novos_registros = 0
            duplicados = 0

            for registro in registros_pagina:
                ticker = registro["Ticker"]
                if ticker not in registros_por_ticker:
                    registros_por_ticker[ticker] = registro
                    novos_registros += 1
                else:
                    duplicados += 1

            print(
                f"  [info] Total acumulado: {len(registros_por_ticker)} | "
                f"Novos na pagina: {novos_registros} | Duplicados ignorados: {duplicados}"
            )

            if not existe_proxima_pagina(driver, pagina_atual):
                break

            pagina_anterior = pagina_atual
            pagina_atual += 1

        salvar_csv(registros_por_ticker, saida)
        print(f"\n[Fim] CSV salvo com {len(registros_por_ticker)} registros em: {saida}")

    except Exception as exc: 
        print(f"\n[erro fatal] O scraping foi interrompido: {exc}")
        raise
    finally:
        if driver is not None:
            driver.quit()
            print("[Encerramento] Navegador fechado corretamente.")


if __name__ == "__main__":
    try:
        executar_scraping()
    except KeyboardInterrupt:
        print("\n[Interrompido] Execucao cancelada pelo usuario.")
        sys.exit(1)
