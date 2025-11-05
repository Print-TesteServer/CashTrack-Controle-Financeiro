import requests
from typing import Optional
from datetime import datetime, timedelta
import json

class CDIService:
    """Serviço para buscar taxa CDI atualizada"""
    
    @staticmethod
    def get_cdi_from_bcb() -> Optional[float]:
        """
        Busca a taxa CDI do Banco Central do Brasil
        Retorna o CDI anual em porcentagem (ex: 10.5 = 10.5% a.a.)
        """
        try:
            # API do Banco Central - CDI acumulado do mês
            # Série 12 = CDI (taxa diária)
            today = datetime.now()
            end_date = today.strftime("%d/%m/%Y")
            start_date = (today - timedelta(days=30)).strftime("%d/%m/%Y")
            
            # Endpoint do Banco Central para CDI
            url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"
            params = {
                "dataInicial": start_date,
                "dataFinal": end_date,
                "formato": "json"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # Pega o último valor (mais recente)
                    latest_value = data[-1]
                    cdi_daily = float(latest_value.get('valor', 0))
                    
                    # BCB retorna CDI diário em porcentagem (ex: 0.04% ao dia)
                    # Para converter para anual: (1 + taxa_diária/100)^252 - 1
                    # Ou aproximação: taxa_diária * 252 (dias úteis)
                    if cdi_daily > 0:
                        # Converte taxa diária para anual
                        # Usando 252 dias úteis (padrão mercado financeiro)
                        cdi_annual = ((1 + cdi_daily / 100) ** 252 - 1) * 100
                        return cdi_annual
        except Exception as e:
            print(f"Erro ao buscar CDI do BCB: {e}")
        
        return None
    
    @staticmethod
    def get_cdi_from_brapi() -> Optional[float]:
        """
        Busca CDI usando API Brapi (alternativa)
        Retorna o CDI anual em porcentagem
        """
        try:
            url = "https://brapi.dev/api/cdi"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Brapi pode retornar array ou objeto
                if isinstance(data, list) and len(data) > 0:
                    # Pega o último valor (mais recente)
                    latest = data[-1]
                    if 'cdi' in latest:
                        cdi_value = float(latest['cdi'])
                        # Validação: CDI anual no Brasil está entre 8-15%
                        # Se for menor que 5, provavelmente está em formato errado
                        if cdi_value < 5:
                            # Se for muito pequeno, pode ser taxa diária ou mensal
                            # Tenta converter: se for diário, multiplica por 252 (dias úteis)
                            # Mas melhor não assumir e retornar None para tentar outra fonte
                            print(f"Aviso: CDI do Brapi ({cdi_value}%) parece estar em formato incorreto")
                            return None
                        return cdi_value
                elif isinstance(data, dict):
                    if 'cdi' in data:
                        cdi_value = float(data['cdi'])
                        if cdi_value < 5:
                            print(f"Aviso: CDI do Brapi ({cdi_value}%) parece estar em formato incorreto")
                            return None
                        return cdi_value
        except Exception as e:
            print(f"Erro ao buscar CDI do Brapi: {e}")
        
        return None
    
    @staticmethod
    def get_current_cdi() -> float:
        """
        Busca CDI atualizado, tentando múltiplas fontes
        Retorna o CDI anual em porcentagem
        Se não conseguir buscar, retorna um valor padrão (10.5% a.a.)
        """
        # Tenta primeiro Banco Central (mais confiável)
        cdi = CDIService.get_cdi_from_bcb()
        
        # Valida o valor do BCB
        if cdi is None or cdi <= 0 or cdi < 5:
            # Tenta Brapi como alternativa
            cdi = CDIService.get_cdi_from_brapi()
        
        # Valida o valor do Brapi
        if cdi is None or cdi <= 0 or cdi < 5:
            # Se ainda não conseguir, usa valor padrão baseado em CDI atual do mercado
            # CDI atual no Brasil (2024) está em torno de 10-12% a.a.
            print("Aviso: Não foi possível buscar CDI atualizado. Usando valor padrão de 10.5% a.a.")
            cdi = 10.5
        
        # Validação final: CDI no Brasil geralmente está entre 8-15% ao ano
        if cdi < 5 or cdi > 20:
            print(f"Aviso: CDI retornado ({cdi}%) está fora do range esperado. Usando valor padrão de 10.5% a.a.")
            cdi = 10.5
        
        print(f"CDI atualizado: {cdi:.2f}% a.a.")
        return cdi
    
    @staticmethod
    def calculate_daily_yield(annual_rate: float) -> float:
        """
        Calcula taxa diária a partir de taxa anual
        Usa 252 dias úteis por ano (padrão mercado financeiro)
        """
        # Taxa diária = (1 + taxa_anual)^(1/252) - 1
        daily_rate = (1 + annual_rate / 100) ** (1/252) - 1
        return daily_rate * 100  # Retorna em porcentagem
    
    @staticmethod
    def calculate_yield_amount(principal: float, annual_rate: float, days: int) -> float:
        """
        Calcula o rendimento acumulado
        principal: valor inicial
        annual_rate: taxa anual em % (ex: 10.5)
        days: número de dias
        """
        if principal <= 0 or annual_rate <= 0 or days <= 0:
            return 0.0
        
        # Taxa diária
        daily_rate = CDIService.calculate_daily_yield(annual_rate) / 100
        
        # Montante final = principal * (1 + taxa_diária)^dias
        final_amount = principal * ((1 + daily_rate) ** days)
        
        # Rendimento = montante - principal
        yield_amount = final_amount - principal
        
        return yield_amount

