import argparse
import json
import os
import sys
import time
from typing import Dict, Any, List, Optional
from tabulate import tabulate
import schedule

from database.db_manager import DatabaseManager
from scrapers.html_scraper import HTMLScraper
from scrapers.manual_collector import ManualCollector
from scrapers.mock_collector import MockCollector
from analytics.price_analyzer import PriceAnalyzer
from analytics.chart_generator import ChartGenerator
from utils.logger import setup_logger

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

logger = setup_logger("Main")

class SneakerPriceTrackerApp:
    def __init__(self, config_path: str = "config/sneakers.json", db_path: str = "database/sneakers.db"):
        self.config_path = config_path
        self.db = DatabaseManager(db_path=db_path)
        self.html_scraper = HTMLScraper()
        self.manual_collector = ManualCollector()
        self.mock_collector = MockCollector()
        self.analyzer = PriceAnalyzer(self.db)
        self.chart_gen = ChartGenerator(self.db)

        self.load_and_sync_config()

    def load_and_sync_config(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.config_path):
            logger.error(f"Arquivo de configuração não encontrado em: {self.config_path}")
            return []

        with open(self.config_path, "r", encoding="utf-8") as f:
            sneakers = json.load(f)

        for s in sneakers:
            self.db.save_sneaker(s)

        logger.info(f"{len(sneakers)} modelos sincronizados com o banco de dados.")
        return sneakers

    def collect_prices(self, use_mock: bool = False) -> None:
        logger.info("Iniciando coleta de preços...")
        sneakers = self.db.get_all_sneakers()

        if use_mock:
            logger.info("Modo MOCK ativado: gerando variação simulada de preços...")

        for sneaker in sneakers:
            sneaker_id = sneaker["id"]
            sneaker_name = f"{sneaker['name']} ({sneaker['colorway']})"

            for source in sneaker.get("sources", []):
                source_name = source["source_name"]
                source_type = source.get("source_type", "manual")
                
                source_cfg = {
                    "sneaker_id": sneaker_id,
                    "name": source_name,
                    "url": source["url"],
                    "css_selector": source.get("css_selector")
                }

                if use_mock:
                    result = self.mock_collector.fetch_price(source_cfg)
                elif source_type == "html":
                    result = self.html_scraper.fetch_price(source_cfg)
                else:
                    result = self.manual_collector.fetch_price(source_cfg)

                if result["price"] is not None:
                    self.db.save_price_record(
                        sneaker_id=sneaker_id,
                        source_name=source_name,
                        price=result["price"],
                        currency="BRL",
                        in_stock=result["in_stock"]
                    )
                    logger.info(f"[{sneaker_name}] Preço salvo para {source_name}: R$ {result['price']:.2f}")
                else:
                    logger.warning(f"[{sneaker_name}] Falha na coleta em {source_name}: {result.get('error')}")

        logger.info("Coleta finalizada.")
        self.check_alerts_and_notify()

    def generate_mock_history(self, days: int = 30) -> None:
        logger.info(f"Populando banco de dados com {days} dias de histórico MOCK para demonstração...")
        sneakers = self.db.get_all_sneakers()
        records = self.mock_collector.generate_historical_dataset(sneakers, days=days)

        for r in records:
            self.db.save_price_record(
                sneaker_id=r["sneaker_id"],
                source_name=r["source_name"],
                price=r["price"],
                currency=r["currency"],
                in_stock=r["in_stock"],
                timestamp=r["timestamp"]
            )

        logger.info("Histórico populado com sucesso.")

    def check_alerts_and_notify(self) -> None:
        alerts = self.analyzer.check_alerts()
        if not alerts:
            logger.info("Nenhum alerta ativado no momento.")
            return

        print("\n" + "="*60)
        print(" 🔔 ALERTAS DE PREÇO ATIVADOS")
        print("="*60)
        for alert in alerts:
            icon = "🎯" if alert["type"] == "TARGET_PRICE_HIT" else "📉"
            print(f"{icon} [{alert['type']}] {alert['sneaker']}: {alert['message']}")
        print("="*60 + "\n")

    def generate_report(self) -> None:
        logger.info("Gerando relatório analítico de preços...")
        summaries = self.analyzer.analyze_all_sneakers()

        if not summaries:
            print("Nenhum dado disponível para exibir no relatório. Execute a coleta primeiro.")
            return

        table_data = []
        for s in summaries:
            target_hit_str = "SIM 🎯" if s["target_hit"] else "NÃO"
            all_time_low_str = "SIM 📉" if s["all_time_low_hit"] else "NÃO"
            table_data.append([
                f"{s['name']}\n({s['colorway']})",
                s['size'],
                f"R$ {s['current_best_price']:.2f}\n[{s['current_best_source']}]",
                f"R$ {s['target_price']:.2f}",
                f"R$ {s['all_time_lowest_price']:.2f}\n[{s['all_time_lowest_source']}]",
                f"{s['discount_from_max_pct']}%",
                target_hit_str
            ])

        headers = ["Modelo", "Tam", "Preço Atual", "Preço Alvo", "Menor da História", "Desconto Max", "Alvo Atingido?"]
        print("\n" + "="*80)
        print(" 👟 SNEAKER PRICE TRACKER - RELATÓRIO EXECUTIVO DE PREÇOS")
        print("="*80)
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
        print("\n")

        # Exibe alertas
        self.check_alerts_and_notify()

        # Gera os gráficos PNG
        self.chart_gen.generate_price_history_chart()
        self.chart_gen.generate_source_comparison_chart()

    def add_sneaker_interactive(self) -> None:
        print("\n--- Cadastro de Novo Tênis para Monitorar ---")
        name = input("Nome do modelo (ex: Nike Dunk Low): ").strip()
        colorway = input("Cor / Colorway (ex: Panda): ").strip()
        size = input("Tamanho BR (padrão: BR 40): ").strip() or "BR 40"
        target_price = float(input("Preço Alvo desejado em R$ (ex: 750.00): ").strip())

        sneaker_id = name.lower().replace(" ", "-") + "-" + colorway.lower().replace(" ", "-")
        sneaker_data = {
            "id": sneaker_id,
            "name": name,
            "colorway": colorway,
            "size": size,
            "target_price": target_price,
            "sources": []
        }

        while True:
            add_src = input("Deseja adicionar uma fonte de preço? (s/n): ").strip().lower()
            if add_src != 's':
                break
            src_name = input("Nome da fonte/loja (ex: StockX, Nike): ").strip()
            src_url = input("URL da página do produto: ").strip()
            src_type = input("Tipo (html/manual): ").strip().lower() or "manual"
            css_sel = None
            if src_type == "html":
                css_sel = input("Seletor CSS do preço (ex: .price): ").strip()

            sneaker_data["sources"].append({
                "name": src_name,
                "url": src_url,
                "type": src_type,
                "css_selector": css_sel
            })

        self.db.save_sneaker(sneaker_data)

        # Atualiza config JSON
        sneakers = self.db.get_all_sneakers()
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(sneakers, f, indent=2, ensure_ascii=False)

        logger.info(f"Tênis '{name}' cadastrado com sucesso e salvo em {self.config_path}.")

    def start_scheduler(self, interval_hours: int = 24) -> None:
        logger.info(f"Agendador ativado. Coletando preços a cada {interval_hours} horas...")
        
        # Executa uma coleta inicial ao agendar
        self.collect_prices(use_mock=True)

        schedule.every(interval_hours).hours.do(self.collect_prices, use_mock=True)

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Agendador encerrado pelo usuário.")

def main():
    parser = argparse.ArgumentParser(description="Sneaker Price Tracker - Ferramenta de Monitoramento de Preços de Tênis")
    parser.add_argument("--collect", action="store_true", help="Executa a coleta de preços atual das fontes")
    parser.add_argument("--mock", action="store_true", help="Usa gerador simulador durante a coleta")
    parser.add_argument("--seed-history", action="store_true", help="Popula o banco de dados com 30 dias de histórico simulado")
    parser.add_argument("--report", action="store_true", help="Gera o relatório executivo e exporta os gráficos PNG")
    parser.add_argument("--add", action="store_true", help="Cadastra interativamente um novo tênis para monitoramento")
    parser.add_argument("--schedule", action="store_true", help="Inicia a execução agendada automática diária")

    args = parser.parse_args()
    app = SneakerPriceTrackerApp()

    if args.seed_history:
        app.generate_mock_history(days=30)
        app.generate_report()
    elif args.collect:
        app.collect_prices(use_mock=args.mock)
    elif args.report:
        app.generate_report()
    elif args.add:
        app.add_sneaker_interactive()
    elif args.schedule:
        app.start_scheduler()
    else:
        # Se nenhum argumento for passado, executa relatório por padrão
        app.generate_report()

if __name__ == "__main__":
    main()
