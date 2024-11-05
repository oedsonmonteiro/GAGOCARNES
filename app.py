from flask import Flask, request, jsonify, send_file
import pandas as pd
import os
import matplotlib.pyplot as plt

app = Flask(__name__)

# Diretório de saída para a planilha e gráficos
OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Caminho do arquivo de saída
output_file = os.path.join(OUTPUT_DIR, 'tabela_despesas.xlsx')

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

# Rota para adicionar despesas em linhas separadas
@app.route('/adicionar_despesas', methods=['POST'])
def adicionar_despesas():
    try:
        data = request.get_json()
        corte = data.get('corte')
        peso = data.get('peso')
        preco = data.get('preco')
        quantidade = data.get('quantidade')
        despesas = data.get('despesas', [])

        # Verificar se as despesas foram fornecidas
        if not despesas:
            return jsonify({"error": "As despesas devem ser fornecidas."}), 400

        # Criar um DataFrame vazio ou carregar existente
        if os.path.exists(output_file):
            df = pd.read_excel(output_file)
        else:
            df = pd.DataFrame(columns=['Descrição', 'Valor (R$)', 'Corte', 'Peso (kg)', 'Preço por Kg (R$)', 'Quantidade'])

        # Adicionar as despesas em linhas separadas
        for despesa in despesas:
            df = pd.concat([df, pd.DataFrame([{
                'Descrição': despesa['descricao'],
                'Valor (R$)': despesa['valor'],
                'Corte': corte,
                'Peso (kg)': peso,
                'Preço por Kg (R$)': preco,
                'Quantidade': quantidade
            }])], ignore_index=True)

        # Salvar a planilha atualizada
        df.to_excel(output_file, index=False)

        return jsonify({"message": "Despesas adicionadas com sucesso!", "arquivo": output_file})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Rota para gerar gráficos dos dados
@app.route('/gerar_graficos', methods=['GET'])
def gerar_graficos():
    try:
        # Carregar a tabela existente
        tabela_path = output_file
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

# Rota para download da planilha
@app.route('/download_planilha', methods=['GET'])
def download_planilha():
    try:
        if os.path.exists(output_file):
            return send_file(output_file, as_attachment=True)
        else:
            return jsonify({"error": "Planilha não encontrada."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
