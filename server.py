import os
import math
import json
from flask import Flask, jsonify, request, send_from_directory
from database.db_manager import DatabaseManager
from analytics.price_analyzer import PriceAnalyzer
from scrapers.mock_collector import MockCollector
from scrapers.search_engine import SneakerSearchEngine
from utils.logger import setup_logger

logger = setup_logger("Server")


def sanitize_json(obj):
    """Recursively replace float NaN/Infinity with None for safe JSON serialization."""
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: sanitize_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_json(v) for v in obj]
    return obj

app = Flask(__name__, static_folder="web", static_url_path="")
db = DatabaseManager("database/sneakers.db")
analyzer = PriceAnalyzer(db)
mock_collector = MockCollector()
search_engine = SneakerSearchEngine()

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
    return jsonify(sanitize_json({
        "status": "online",
        "timestamp": os.popen("date /t").read().strip() if os.name == "nt" else "",
        "summaries": summaries,
        "alerts": alerts
    }))

@app.route("/api/history", methods=["GET"])
def get_history():
    sneaker_id = request.args.get("sneaker_id")
    df = db.get_price_history_dataframe(sneaker_id=sneaker_id)
    if df.empty:
        return jsonify([])
    
    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    records = df.where(df.notna(), other=None).to_dict(orient="records")
    return jsonify(sanitize_json(records))

@app.route("/api/search", methods=["GET"])
def search_sneakers():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify(search_engine.search(""))

    cached = db.get_search_cache(query)
    if cached:
        logger.info(f"Retornando busca para '{query}' a partir do cache SQLite.")
        return jsonify(cached)

    results = search_engine.search(query)
    db.save_search_cache(query, results)
    return jsonify(results)

@app.route("/api/sneakers/pin", methods=["POST"])
def pin_sneaker():
    data = request.json
    if not data or "id" not in data:
        return jsonify({"success": False, "error": "Dados do tênis inválidos"}), 400

    sneaker_id = data["id"]
    db.pin_sneaker(data)

    # Popula histórico de 30 dias para o novo tênis fixado se não houver histórico
    df_existing = db.get_price_history_dataframe(sneaker_id=sneaker_id)
    if df_existing.empty:
        records = mock_collector.generate_historical_dataset([data], days=30)
        for r in records:
            db.save_price_record(
                sneaker_id=r["sneaker_id"],
                source_name=r["source_name"],
                price=r["price"],
                currency=r["currency"],
                in_stock=r["in_stock"],
                timestamp=r["timestamp"]
            )

    return jsonify({"success": True, "message": f"Tênis '{data['name']}' fixado com sucesso."})

@app.route("/api/sneakers/pin/<sneaker_id>", methods=["DELETE"])
def unpin_sneaker(sneaker_id):
    db.unpin_sneaker(sneaker_id)
    return jsonify({"success": True, "message": f"Tênis ID '{sneaker_id}' desafixado do radar."})

@app.route("/api/sneakers/pinned", methods=["GET"])
def get_pinned():
    sneakers = db.get_all_sneakers(pinned_only=True)
    return jsonify(sanitize_json(sneakers))

@app.route("/api/collect", methods=["POST"])
def trigger_collect():
    use_mock = request.json.get("mock", True) if request.json else True
    sneakers = db.get_all_sneakers(pinned_only=True)

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
    return jsonify(sanitize_json({
        "success": True,
        "collected_records": collected_count,
        "summaries": summaries,
        "alerts": alerts
    }))

@app.route("/api/seed", methods=["POST"])
def seed_data():
    days = request.json.get("days", 30) if request.json else 30
    sneakers = db.get_all_sneakers(pinned_only=True)
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
    print("🚀 Servidor Sneaker Pulse Command Center em http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
