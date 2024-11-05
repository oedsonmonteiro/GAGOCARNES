from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import os
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Diretório de saída para a planilha e gráficos
OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Caminho do arquivo de saída
output_file = os.path.join(OUTPUT_DIR, 'tabela_despesas.xlsx')

@app.route('/importar_csv', methods=['POST'])
def importar_csv():
    try:
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nenhum arquivo enviado"}), 400
        df = pd.read_csv(file)
        imported_file = os.path.join(OUTPUT_DIR, 'tabela_importada.xlsx')
        df.to_excel(imported_file, index=False)
        return jsonify({"message": "Arquivo CSV importado com sucesso!", "arquivo": imported_file})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/adicionar_despesas', methods=['POST'])
def adicionar_despesas():
    try:
        data = request.get_json()
        corte = data.get('corte')
        despesas = data.get('despesas', [])
        df = pd.DataFrame(columns=['Descrição', 'Valor (R$)', 'Corte'])
        for despesa in despesas:
            df = pd.concat([df, pd.DataFrame([{'Descrição': despesa['descricao'], 'Valor (R$)': despesa['valor'], 'Corte': corte}])], ignore_index=True)
        df.to_excel(output_file, index=False)
        return jsonify({"message": "Despesas adicionadas com sucesso!", "arquivo": output_file})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/gerar_graficos', methods=['GET'])
def gerar_graficos():
    try:
        df = pd.read_excel(output_file)
        graficos = []
        for coluna in df.select_dtypes(include='number').columns:
            plt.figure()
            df[coluna].plot(kind='bar', title=coluna)
            buf = BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            image_base64 = base64.b64encode(buf.read()).decode('utf-8')
            graficos.append({"coluna": coluna, "imagem": image_base64})
        return jsonify({"message": "Gráficos gerados com sucesso!", "graficos": graficos})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download_planilha', methods=['GET'])
def download_planilha():
    try:
        if os.path.exists(output_file):
            return send_file(output_file, as_attachment=True)
        else:
            return jsonify({"error": "Planilha não encontrada."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ver_planilha', methods=['GET'])
def ver_planilha():
    try:
        if os.path.exists(output_file):
            df = pd.read_excel(output_file)
            df_relevantes = df[['Descrição', 'Valor (R$)', 'Corte']]
            return df_relevantes.to_html(index=False, border=0, classes='table table-striped')
        else:
            return jsonify({"error": "Planilha não encontrada."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
