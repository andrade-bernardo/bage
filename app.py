from flask import Flask, render_template, request, redirect, url_for, flash, session
import json
import os
from sheets import enviar_para_google_sheets, carregar_dados, salvar_dados

app = Flask(__name__)
app.secret_key = "segredo"  # Usado para sessões (flash messages)

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
    
    total_uruguaiana = sum(registro['litros'] for registro in registros_uruguaiana)
    total_bage = sum(registro['litros'] for registro in registros_bage)
    
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
    total_litros = sum(registro['litros'] for registro in registros)
    
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
        salvar_dados(dados)
        flash('Registro atualizado com sucesso!', 'success')
        return redirect(url_for('admin_dashboard'))  # Redireciona para a página de admin após edição
    
    return render_template('editar.html', registro=registro)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Usa a variável de ambiente PORT
    app.run(debug=False, host='0.0.0.0', port=port)
