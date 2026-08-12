# 👟 Sneaker Price Tracker

**Sneaker Price Tracker** é uma ferramenta em Python desenvolvida para monitorar o histórico de preços de modelos de tênis específicos ao longo do tempo (como **Nike Zoom Vomero 5**, Air Force 1, Dunk Low, entre outros) em diferentes fontes e e-commerces, armazenando os dados em banco local SQLite e gerando relatórios com gráficos analíticos e alertas de menor preço registrado.

---

## 🎯 Funcionalidades Principais

- **Cadastro Personalizado**: Monitoramento configurável por modelo, cor, tamanho (padrão **BR 40**) e preço-alvo.
- **Coleta Multi-Fonte**: Suporte a coletores HTML parametrizáveis, entrada manual/batch para lojas protegidas por anti-bot (StockX, Nike) e gerador de dados históricos simulados para testes de portfólio.
- **Armazenamento Persistente**: Banco de dados SQLite portátil local (`database/sneakers.db`).
- **Análise & Relatórios Analíticos**: Relatório executivo via linha de comando (CLI) utilizando `pandas` e `tabulate`.
- **Gráficos de Evolução**: Exportação automática de gráficos de linha temporais e barras comparativas (`matplotlib`).
- **Sistema de Alertas**: Detecção de preço-alvo atingido (`TARGET_PRICE_HIT`) e menor preço histórico registrado (`ALL_TIME_LOW`).
- **Agendamento Automático**: Execução programada diária (`schedule`).

---

## 📁 Arquitetura do Projeto

```
sneaker-price-tracker/
├── config/
│   └── sneakers.json           # Lista de tênis monitorados e fontes
├── database/
│   ├── schema.sql              # Schema DDL do SQLite
│   └── db_manager.py           # Gerenciador do SQLite (DAO)
├── scrapers/
│   ├── base_scraper.py         # Classe abstrata para coletores
│   ├── html_scraper.py         # Coletor genérico HTML via BeautifulSoup
│   ├── manual_collector.py     # Coletor para entrada manual / batch
│   └── mock_collector.py       # Gerador de histórico simulado (30 dias)
├── analytics/
│   ├── price_analyzer.py       # Processamento estatístico Pandas & alertas
│   └── chart_generator.py      # Geração dos gráficos Matplotlib
├── utils/
│   └── logger.py               # Configuração de logs
├── tests/
│   └── test_tracker.py         # Suíte de testes unitários (unittest)
├── reports/
│   ├── price_history_all.png   # Gráfico de evolução temporal
│   └── source_comparison.png   # Gráfico de comparação entre lojas
├── main.py                     # Ponto de entrada CLI e agendamento
├── requirements.txt            # Dependências do projeto
├── .gitignore                  # Arquivos ignorados pelo Git
└── README.md                   # Documentação completa
```

---

## ⚖️ Conformidade com Termos de Uso e Scraping

De acordo com as boas práticas de web scraping e verificação dos arquivos `robots.txt`:
- **StockX e Nike BR**: Possuem proteção por WAF (Cloudflare 403) e proíbem crawling automatizado nos seus Termos de Serviço. O projeto utiliza para estas fontes um **Módulo de Coleta Manual/Batch** ou **Dados Simulados Mock**.
- **Lojas com Páginas Públicas**: O módulo `HTMLScraper` permite configurar seletores CSS para lojas públicas que permitam indexação respeitando delay entre requisições.

---

## 🚀 Como Instalar e Rodar

### 1. Clocar o repositório e preparar o ambiente

```bash
git clone https://github.com/henriqueDias57/sneaker-price-tracker.git
cd sneaker-price-tracker

# Criar ambiente virtual (opcional, mas recomendado)
python -m venv venv
# No Windows:
venv\Scripts\activate
# No Linux/macOS:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

---

## 🛠️ Comandos de Uso

### 1. Gerar dados de teste (30 dias) e visualizar relatórios
Para popular o banco com dados históricos de demonstração para o seu portfólio:
```bash
python main.py --seed-history
```

### 2. Executar a coleta de preços atual
```bash
python main.py --collect --mock
```

### 3. Exibir relatório no terminal e exportar gráficos PNG
```bash
python main.py --report
```

### 4. Cadastrar um novo tênis para monitorar
```bash
python main.py --add
```

### 5. Executar o agendador diário automático
```bash
python main.py --schedule
```

### 6. Executar os testes unitários
```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 📊 Exemplo de Output do Relatório

```text
================================================================================
 👟 SNEAKER PRICE TRACKER - RELATÓRIO EXECUTIVO DE PREÇOS
================================================================================
+-----------------------------------+-------+----------------------+--------------+----------------------+--------------+----------------+
| Modelo                            | Tam   | Preço Atual          | Preço Alvo   | Menor da História    | Desconto Max | Alvo Atingido? |
+-----------------------------------+-------+----------------------+--------------+----------------------+--------------+----------------+
| Nike Zoom Vomero 5                | BR 40 | R$ 945.20            | R$ 950.00    | R$ 892.50            | 21.2%        | SIM 🎯         |
| (Cobblestone / Flat Pewter)       |       | [StockX]             |              | [StockX]             |              |                |
+-----------------------------------+-------+----------------------+--------------+----------------------+--------------+----------------+
| Nike Air Force 1 '07              | BR 40 | R$ 685.00            | R$ 700.00    | R$ 660.00            | 14.3%        | SIM 🎯         |
| (Triple White)                    |       | [StockX]             |              | [Centauro]           |              |                |
+-----------------------------------+-------+----------------------+--------------+----------------------+--------------+----------------+
| Nike Dunk Low                     | BR 40 | R$ 810.00            | R$ 800.00    | R$ 790.00            | 18.9%        | NÃO            |
| (Black White (Panda))             |       | [StockX]             |              | [StockX]             |              |                |
+-----------------------------------+-------+----------------------+--------------+----------------------+--------------+----------------+

============================================================
 🔔 ALERTAS DE PREÇO ATIVADOS
============================================================
🎯 [TARGET_PRICE_HIT] Nike Zoom Vomero 5 (Cobblestone / Flat Pewter): Preço alvo atingido! Atual: R$ 945.20 (Alvo: R$ 950.00) na loja StockX
🎯 [TARGET_PRICE_HIT] Nike Air Force 1 '07 (Triple White): Preço alvo atingido! Atual: R$ 685.00 (Alvo: R$ 700.00) na loja StockX
============================================================
```

Os gráficos gerados são salvos automaticamente na pasta `reports/`:
- `reports/price_history_all.png`: Linhas do tempo mostrando flutuação diária.
- `reports/source_comparison.png`: Gráfico de barras comparando os preços entre lojas.

---

## 📌 Limitações Atuais & Evoluções Futuras

- **Limitações**:
  - Lojas com Cloudflare WAF rigoroso requerem inserção manual ou uso de soluções de scraping com browser headless (Selenium/Playwright com proxies residenciais).
- **Próximos Passos**:
  - Adicionar suporte a notificações via Telegram Bot ou Webhook do Discord.
  - Implementar interface web interativa em Streamlit/Dash para visualização do histórico.
