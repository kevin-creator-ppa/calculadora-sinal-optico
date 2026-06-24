# Calculadora de Sinal Óptico - Telium

Aplicação Streamlit para cálculo e validação de potência óptica em enlaces de fibra óptica.

## Recursos

- Cálculo de perda óptica em ambos os sentidos (A→B e B→A)
- Validação de TX/RX e budget de GBICs
- Leitura de GBICs a partir de `gbics.csv`
- Histórico local em `history.json`
- Exportação de relatório em PDF
- Exportação de histórico em CSV
- Tema escuro forçado e ocultação do botão Deploy

## Como usar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Execute a aplicação:
   ```bash
   python app.py
   ```
3. Abra o navegador em `http://localhost:8501`.

## Arquivos principais

- `app.py` - aplicação principal
- `gbics.csv` - base de dados de GBICs
- `history.json` - histórico de cálculos
- `assets/watermark-base64.txt` - marca d'água em base64

## Observações

- Se `gbics.csv` estiver incompleto, a aplicação exibirá um alerta.
- O histórico é limitado aos últimos 20 cálculos.

