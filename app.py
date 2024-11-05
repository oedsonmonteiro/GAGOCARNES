from flask import Flask, request, jsonify, send_file
import pandas as pd
import os
import matplotlib.pyplot as plt

app = Flask(__name__)

# Diretório de saída para a planilha e gráficos
OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Rota para importar e visualizar uma tabela CSV
@app.route('/importar_csv', methods=['POST'])
def importar_csv():
    try:
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nenhum arquivo enviado"}), 400

        # Importar a tabela CSV
        df = pd.read_csv(file)
        
        # Salvar uma cópia da tabela importada
        imported_file = os.path.join(OUTPUT_DIR, 'tabela_importada.xlsx')
        df.to_excel(imported_file, index=False)

        return jsonify({"message": "Arquivo CSV importado com sucesso!", "arquivo": imported_file})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Rota para adicionar colunas e linhas sincronizadas com a calculadora
@app.route('/adicionar_coluna_linha', methods=['POST'])
def adicionar_coluna_linha():
    try:
        data = request.get_json()
        coluna_nome = data.get('coluna_nome')
        linha_dados = data.get('linha_dados', {})
        
        # Verificar se a coluna e os dados foram fornecidos
        if not coluna_nome or not linha_dados:
            return jsonify({"error": "Nome da coluna e dados da linha são obrigatórios."}), 400

        # Carregar a tabela existente
        tabela_path = os.path.join(OUTPUT_DIR, 'tabela_importada.xlsx')
        if not os.path.exists(tabela_path):
            return jsonify({"error": "Tabela não encontrada. Importe primeiro um arquivo CSV."}), 404

        df = pd.read_excel(tabela_path)

        # Adicionar a nova coluna se não existir
        if coluna_nome not in df.columns:
            df[coluna_nome] = ''

        # Adicionar a nova linha com os dados sincronizados
        new_row = pd.Series(linha_dados, index=df.columns)
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        # Salvar a tabela atualizada
        tabela_atualizada_path = os.path.join(OUTPUT_DIR, 'tabela_atualizada.xlsx')
        df.to_excel(tabela_atualizada_path, index=False)

        return jsonify({"message": "Coluna e linha adicionadas com sucesso!", "arquivo": tabela_atualizada_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Rota para gerar gráficos dos dados
@app.route('/gerar_graficos', methods=['GET'])
def gerar_graficos():
    try:
        # Carregar a tabela existente
        tabela_path = os.path.join(OUTPUT_DIR, 'tabela_atualizada.xlsx')
        if not os.path.exists(tabela_path):
            return jsonify({"error": "Tabela não encontrada. Importe ou atualize um arquivo."}), 404

        df = pd.read_excel(tabela_path)

        # Criar gráficos para colunas numéricas
        for coluna in df.select_dtypes(include='number').columns:
            plt.figure()
            df[coluna].plot(kind='bar', title=coluna)
            plt.xlabel('Índice')
            plt.ylabel(coluna)
            grafico_path = os.path.join(OUTPUT_DIR, f'grafico_{coluna}.png')
            plt.savefig(grafico_path)
            plt.close()

        return jsonify({"message": "Gráficos gerados com sucesso!", "diretorio_graficos": OUTPUT_DIR})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
