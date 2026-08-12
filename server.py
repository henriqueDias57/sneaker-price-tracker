import os
import json
from flask import Flask, jsonify, request, send_from_directory
from database.db_manager import DatabaseManager
from analytics.price_analyzer import PriceAnalyzer
from scrapers.mock_collector import MockCollector
from utils.logger import setup_logger

logger = setup_logger("Server")

app = Flask(__name__, static_folder="web", static_url_path="")
db = DatabaseManager("database/sneakers.db")
analyzer = PriceAnalyzer(db)
mock_collector = MockCollector()

@app.route("/")
def index():
    return send_from_directory("web", "index.html")

@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory("web", path)

@app.route("/api/summary", methods=["GET"])
def get_summary():
    summaries = analyzer.analyze_all_sneakers()
    alerts = analyzer.check_alerts()
    return jsonify({
        "status": "online",
        "timestamp": os.popen("date /t").read().strip() if os.name == "nt" else "",
        "summaries": summaries,
        "alerts": alerts
    })

@app.route("/api/history", methods=["GET"])
def get_history():
    sneaker_id = request.args.get("sneaker_id")
    df = db.get_price_history_dataframe(sneaker_id=sneaker_id)
    if df.empty:
        return jsonify([])
    
    # Formata timestamps para string ISO para consumo no Chart.js
    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    records = df.to_dict(orient="records")
    return jsonify(records)

@app.route("/api/collect", methods=["POST"])
def trigger_collect():
    use_mock = request.json.get("mock", True) if request.json else True
    sneakers = db.get_all_sneakers()

    collected_count = 0
    for sneaker in sneakers:
        sneaker_id = sneaker["id"]
        for source in sneaker.get("sources", []):
            source_name = source["source_name"]
            source_cfg = {
                "sneaker_id": sneaker_id,
                "name": source_name,
                "url": source["url"]
            }
            res = mock_collector.fetch_price(source_cfg)
            if res["price"]:
                db.save_price_record(sneaker_id, source_name, res["price"])
                collected_count += 1

    summaries = analyzer.analyze_all_sneakers()
    alerts = analyzer.check_alerts()
    return jsonify({
        "success": True,
        "collected_records": collected_count,
        "summaries": summaries,
        "alerts": alerts
    })

@app.route("/api/seed", methods=["POST"])
def seed_data():
    days = request.json.get("days", 30) if request.json else 30
    sneakers = db.get_all_sneakers()
    records = mock_collector.generate_historical_dataset(sneakers, days=days)
    for r in records:
        db.save_price_record(
            sneaker_id=r["sneaker_id"],
            source_name=r["source_name"],
            price=r["price"],
            currency=r["currency"],
            in_stock=r["in_stock"],
            timestamp=r["timestamp"]
        )
    return jsonify({"success": True, "records_added": len(records)})

if __name__ == "__main__":
    print("🚀 Iniciando Servidor Sneaker Pulse Command Center em http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
