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

# Rota para adicionar despesas em linhas separadas
@app.route('/adicionar_despesas', methods=['POST'])
def adicionar_despesas():
    try:
        logger.info("Recebendo dados para adicionar despesas.")
        data = request.get_json()
        if not data:
            logger.warning("Dados da requisição vazios ou inválidos.")
            return jsonify({"error": "Corpo da requisição vazio ou dados inválidos."}), 400

        corte = data.get('corte')
        despesas = data.get('despesas', [])

        if not despesas:
            logger.warning("Nenhuma despesa fornecida.")
            return jsonify({"error": "As despesas devem ser fornecidas."}), 400

        # Criar um novo DataFrame para armazenar as despesas
        df = pd.DataFrame(columns=['Descrição', 'Valor (R$)', 'Corte'])

        # Adicionar as despesas em linhas separadas
        for despesa in despesas:
            df = pd.concat([df, pd.DataFrame([{
                'Descrição': despesa['descricao'],
                'Valor (R$)': despesa['valor'],
                'Corte': corte
            }])], ignore_index=True)

        # Salvar a planilha com os novos dados, sobrescrevendo a anterior
        df.to_excel(output_file, index=False)
        logger.info("Despesas adicionadas e arquivo salvo com sucesso.")

        return jsonify({"message": "Despesas adicionadas com sucesso!", "arquivo": output_file})
    except Exception as e:
        logger.error(f"Erro ao adicionar despesas: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Rota para visualizar a planilha como HTML
@app.route('/ver_planilha', methods=['GET'])
def ver_planilha():
    try:
        logger.info("Solicitação para visualizar a planilha.")
        if os.path.exists(output_file):
            df = pd.read_excel(output_file)
            # Selecionar apenas as colunas relevantes
            df_relevantes = df[['Descrição', 'Valor (R$)', 'Corte']]
            return df_relevantes.to_html(index=False, border=0, classes='table table-striped')
        else:
            logger.warning("Planilha não encontrada.")
            return jsonify({"error": "Planilha não encontrada."}), 404
    except Exception as e:
        logger.error(f"Erro ao visualizar a planilha: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# As demais rotas permanecem inalteradas...

if __name__ == '__main__':
    logger.info("Iniciando a aplicação Flask.")
    app.run(host='0.0.0.0', port=5000)
