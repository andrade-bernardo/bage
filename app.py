from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import json
import os
from openpyxl import Workbook
import csv

# Inicializa o Flask
app = Flask(__name__)
app.secret_key = "segredo"  # Usado para sessões (flash messages)

# Função para carregar os dados (registros de abastecimento)
def carregar_dados():
    try:
        with open('abastecimentos.json', 'r') as file:
            dados = json.load(file)
    except FileNotFoundError:
        dados = []  # Se o arquivo não for encontrado, retorna uma lista vazia
    return dados

# Função para salvar os dados no arquivo JSON
def salvar_dados(dados):
    with open('abastecimentos.json', 'w') as file:
        json.dump(dados, file, indent=4)

# Função para gerar o arquivo .xlsx
def exportar_para_excel(dados):
    wb = Workbook()
    ws = wb.active
    ws.title = "Abastecimento"
    
    # Cabeçalho da planilha
    cabecalho = ['ID', 'Base', 'Data', 'Ônibus', 'Litros', 'Responsável', 'Hodômetro']
    ws.append(cabecalho)

    # Adicionando os registros na planilha
    for registro in dados:
        ws.append([registro['id'], registro['base'], registro['data'], registro['onibus'], registro['litros'], registro['responsavel'], registro['hodometro']])
    
    # Caminho do arquivo
    caminho_arquivo = "dados_abastecimento.xlsx"
    wb.save(caminho_arquivo)

    return caminho_arquivo

# Função para gerar o arquivo .csv
def exportar_para_csv(dados):
    caminho_arquivo = "dados_abastecimento.csv"
    
    # Abre o arquivo CSV para escrita
    with open(caminho_arquivo, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['ID', 'Base', 'Data', 'Ônibus', 'Litros', 'Responsável', 'Hodômetro'])
        
        # Adiciona os registros
        for registro in dados:
            writer.writerow([registro['id'], registro['base'], registro['data'], registro['onibus'], registro['litros'], registro['responsavel'], registro['hodometro']])
    
    return caminho_arquivo

# Rota para exportar dados como .xlsx
@app.route('/exportar_excel/<base>', methods=['GET'])
def exportar_excel(base):
    dados = carregar_dados()  # Carrega os dados
    registros_base = [registro for registro in dados if registro['base'] == base]
    
    # Chama a função de exportação
    caminho_arquivo = exportar_para_excel(registros_base)
    
    # Envia o arquivo para download
    return send_file(caminho_arquivo, as_attachment=True)

# Rota para exportar dados como .csv
@app.route('/exportar_csv/<base>', methods=['GET'])
def exportar_csv(base):
    dados = carregar_dados()  # Carrega os dados
    registros_base = [registro for registro in dados if registro['base'] == base]
    
    # Chama a função de exportação
    caminho_arquivo = exportar_para_csv(registros_base)
    
    # Envia o arquivo para download
    return send_file(caminho_arquivo, as_attachment=True)

# Dicionário de bases e senhas com tipo de usuário
bases_senhas = {
    "admin": {"senha": "admin123", "tipo": "admin"},
    "uruguaiana": {"senha": "senhaUruguaiana", "tipo": "base"},
    "bage": {"senha": "senhaBage", "tipo": "base"}
}

# Página de login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        base = request.form['base']
        senha = request.form['senha']
        
        # Verifica se as credenciais são válidas
        if base in bases_senhas and bases_senhas[base]["senha"] == senha:
            tipo_usuario = bases_senhas[base]["tipo"]
            
            # Armazena a base e o tipo de usuário na sessão
            session['base'] = base
            session['tipo_usuario'] = tipo_usuario
            
            # Redireciona com base no tipo de usuário
            if tipo_usuario == "admin":
                return redirect(url_for('admin_dashboard'))  # Página de admin
            elif tipo_usuario == "base":
                return redirect(url_for('dashboard', base=base))  # Página da base (Uruguaiana ou Bagé)
        else:
            flash('Credenciais inválidas', 'error')
    
    return render_template('login.html')

# Função de logout
@app.route('/logout')
def logout():
    # Remove as variáveis da sessão
    session.clear()
    flash('Você foi desconectado com sucesso!', 'success')
    return redirect(url_for('login'))

# Página do dashboard do admin
@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'tipo_usuario' not in session or session['tipo_usuario'] != 'admin':
        return redirect(url_for('login'))  # Redireciona para login se não for admin
    
    # Carrega os dados de abastecimento
    dados = carregar_dados()
    
    # Filtra registros das bases
    registros_uruguaiana = [registro for registro in dados if registro['base'] == 'uruguaiana']
    registros_bage = [registro for registro in dados if registro['base'] == 'bage']
    
    # Força a conversão para float e soma os litros
    total_uruguaiana = sum([float(registro['litros']) if isinstance(registro['litros'], (int, float)) else 0 for registro in registros_uruguaiana])
    total_bage = sum([float(registro['litros']) if isinstance(registro['litros'], (int, float)) else 0 for registro in registros_bage])
    
    return render_template('admin_dashboard.html', 
                           registros_uruguaiana=registros_uruguaiana, 
                           registros_bage=registros_bage, 
                           total_uruguaiana=total_uruguaiana, 
                           total_bage=total_bage)

# Alteração da lógica para ver os registros sem precisar de login nas bases
@app.route('/dashboard/<base>', methods=['GET', 'POST'])
def dashboard(base):
    if 'tipo_usuario' not in session or session['tipo_usuario'] not in ['base', 'admin']:
        return redirect(url_for('login'))  # Redireciona para login se não for admin ou base
    
    # Carrega os registros de abastecimento para a base
    dados = carregar_dados()
    registros = [registro for registro in dados if registro['base'] == base]

    if request.method == 'POST':
        # Pegando os dados do formulário
        data = request.form['data']
        onibus = request.form['onibus']
        litros = float(request.form['litros'])
        responsavel = request.form['responsavel']
        hodometro = float(request.form['hodometro'])  # Campo do hodômetro
        
        # Criação de um novo registro
        novo_registro = {
            'id': len(dados) + 1,  # ID único
            'base': base,
            'data': data,
            'onibus': onibus,
            'litros': litros,
            'responsavel': responsavel,
            'hodometro': hodometro  # Adicionando o hodômetro
        }
        
        # Adiciona o novo registro à lista de dados
        dados.append(novo_registro)
        
        # Salva os dados atualizados no arquivo JSON
        salvar_dados(dados)
        
        # Redireciona para a página de dashboard novamente, com dados atualizados
        return redirect(url_for('dashboard', base=base))  # Redireciona para a página atualizada

    # Calcula o total de litros abastecidos
    total_litros = sum([float(registro['litros']) if isinstance(registro['litros'], (int, float)) else 0 for registro in registros])
    
    return render_template('dashboard.html', base=base, registros=registros, total_litros=total_litros)

# Excluir um registro
@app.route('/delete/<base>/<int:id>', methods=['GET'])
def delete_registro(base, id):
    dados = carregar_dados()
    dados = [registro for registro in dados if not (registro['base'] == base and registro['id'] == id)]
    salvar_dados(dados)
    flash('Registro excluído com sucesso!', 'success')
    return redirect(url_for('admin_dashboard'))  # Redireciona para a página de admin após exclusão

# Editar um registro
@app.route('/edit/<base>/<int:id>', methods=['GET', 'POST'])
def edit_registro(base, id):
    dados = carregar_dados()
    registro = next((r for r in dados if r['base'] == base and r['id'] == id), None)
    
    if request.method == 'POST':
        registro['data'] = request.form['data']
        registro['onibus'] = request.form['onibus']
        registro['litros'] = float(request.form['litros'])
        registro['responsavel'] = request.form['responsavel']
        registro['hodometro'] = float(request.form['hodometro'])  # Atualizando o hodômetro
        salvar_dados(dados)
        flash('Registro atualizado com sucesso!', 'success')
        return redirect(url_for('admin_dashboard'))  # Redireciona para a página de admin após edição
    
    return render_template('editar.html', registro=registro)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Usa a variável de ambiente PORT
    app.run(debug=True, host='0.0.0.0', port=port)  # Habilitando o debug
