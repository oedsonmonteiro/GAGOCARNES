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

# Rota para adicionar despesas
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

        # Formatando a planilha como uma tabela
        with pd.ExcelWriter(output_file, engine='openpyxl', mode='a') as writer:
            df.to_excel(writer, sheet_name='Despesas', index=False)
            worksheet = writer.sheets['Despesas']
            table = writer.book.add_table(worksheet.dimensions, 'TabelaDespesas', 'Despesas', 'Tabela de Despesas', style='TableStyleMedium9')

        logger.info("Despesas adicionadas e arquivo salvo com sucesso.")
        return jsonify({"message": "Despesas adicionadas com sucesso!", "arquivo": output_file})
    except Exception as e:
        logger.error(f"Erro ao adicionar despesas: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Rota para gerar gráficos dos dados
@app.route('/gerar_graficos', methods=['GET'])
def gerar_graficos():
    try:
        logger.info("Gerando gráficos a partir dos dados.")
        if not os.path.exists(output_file):
            logger.warning("Tabela de despesas não encontrada.")
            return jsonify({"error": "Tabela não encontrada. Importe ou atualize um arquivo."}), 404

        df = pd.read_excel(output_file)
        graficos = []

        for coluna in df.select_dtypes(include='number').columns:
            plt.figure()
            df[coluna].plot(kind='bar', title=coluna)
            plt.xlabel('Índice')
            plt.ylabel(coluna)

            buf = BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            image_base64 = base64.b64encode(buf.read()).decode('utf-8')
            logger.info(f"Gráfico gerado para a coluna {coluna}.")
            graficos.append({"coluna": coluna, "imagem": image_base64})

        logger.info("Todos os gráficos gerados com sucesso.")
        return jsonify({"message": "Gráficos gerados com sucesso!", "graficos": graficos})
    except Exception as e:
        logger.error(f"Erro ao gerar gráficos: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Rota para download da planilha
@app.route('/download_planilha', methods=['GET'])
def download_planilha():
    try:
        logger.info("Solicitação de download da planilha.")
        if os.path.exists(output_file):
            logger.info("Planilha encontrada e enviada para download.")
            return send_file(output_file, as_attachment=True)
        else:
            logger.warning("Planilha não encontrada.")
            return jsonify({"error": "Planilha não encontrada."}), 404
    except Exception as e:
        logger.error(f"Erro ao baixar a planilha: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Iniciando a aplicação Flask.")
    app.run(host='0.0.0.0', port=5000)
