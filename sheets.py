import gspread
from google.oauth2.service_account import Credentials
import json

# Escopo correto para acessar e editar planilhas no Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Carregar credenciais e autorizar
def obter_credenciais():
    try:
        # Carrega as credenciais do arquivo
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        return creds
    except Exception as e:
        print(f"Erro ao carregar as credenciais: {e}")
        return None

# Enviar dados para o Google Sheets
def enviar_para_google_sheets(dados):
    creds = obter_credenciais()
    if not creds:
        return False  # Se não conseguiu obter as credenciais, retorna False
    
    try:
        # Autentica o cliente com as credenciais
        client = gspread.authorize(creds)
        
        # Tenta abrir a planilha "Controle de Abastecimento"
        try:
            sheet = client.open('Controle de Abastecimento').sheet1
        except gspread.exceptions.SpreadsheetNotFound:
            print("A planilha 'Controle de Abastecimento' não foi encontrada.")
            # Se não existir, cria uma nova planilha
            sheet = client.create('Controle de Abastecimento').sheet1
            sheet.append_row(['Data', 'Motorista', 'Litros', 'Valor', 'Base'])  # Adiciona cabeçalho

        # Adiciona os dados do abastecimento na planilha
        sheet.append_row([dados['data'], dados['motorista'], dados['litros'], dados['valor'], dados['base']])
        return True  # Sucesso ao adicionar na planilha
    except gspread.exceptions.APIError as e:
        print(f"Erro ao acessar a planilha: {e}")
        return False  # Se houve erro ao acessar a planilha, retorna False

# Carregar dados do arquivo JSON
def carregar_dados():
    try:
        with open('abastecimentos.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Salvar dados no arquivo JSON
def salvar_dados(dados):
    try:
        with open('abastecimentos.json', 'w') as f:
            json.dump(dados, f, indent=4)
    except Exception as e:
        print(f"Erro ao salvar os dados no arquivo: {e}")
