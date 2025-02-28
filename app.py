from flask import Flask, jsonify, render_template, request, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from scraper import (
    get_flights_enuygun_playwright,
    get_flights_turna_oneway_playwright,
    simulate_purchase_enuygun,
    simulate_purchase_turna
)

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.config["DEBUG"] = True

limiter = Limiter(get_remote_address, app=app, default_limits=["2 per second"])


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/flights", methods=["GET"])
def flights():
    kalkis = request.args.get("kalkis", "ankara-esenboga-havalimani")
    varis = request.args.get("varis", "istanbul-sabiha-gokcen-havalimani")
    kalkis_kodu = request.args.get("kalkis_kodu", "esb")
    varis_kodu = request.args.get("varis_kodu", "ista")
    tarih = request.args.get("tarih", "2025-02-28")

    logging.info(f"🔍 Arama: {kalkis} ({kalkis_kodu}) → {varis} ({varis_kodu}) | Tarih: {tarih}")

    try:
        enuygun = get_flights_enuygun_playwright(kalkis, varis, kalkis_kodu, varis_kodu, tarih)
        turna = get_flights_turna_oneway_playwright(kalkis, varis, tarih)
        all_flights = enuygun + turna
        return jsonify(all_flights)
    except Exception as e:
        logging.error(f"Uçuş verileri alınırken hata oluştu: {e}")
        return jsonify({"error": "Uçuş verileri alınırken hata oluştu", "details": str(e)}), 500


@app.route("/purchase/enuygun", methods=["GET"])
def purchase_enuygun():
    try:
        flight_id = request.args.get("flight_id")
        request_id = request.args.get("request_id")
        logging.info(f"❕ Enuygun satın alma isteği: flight_id={flight_id}, request_id={request_id}")
        final_url = simulate_purchase_enuygun(flight_id, request_id)
        if "odeme" in final_url:
            return jsonify({"final_url": final_url})
        else:
            return jsonify({"error": "Satın alma işlemi başarısız oldu."}), 500
    except Exception as e:
        logging.error(f"❌ Satın alma hatası: {e}")
        return jsonify({"error": "Satın alma işlemi sırasında bir hata oluştu."}), 500


@app.route("/purchase/turna", methods=["GET"])
def purchase_turna():
    try:
        flight_id = request.args.get("flight_id")
        logging.info(f"❕ Turna satın alma isteği: flight_id={flight_id}")
        final_url = simulate_purchase_turna(flight_id)
        return redirect(final_url)
    except Exception as e:
        logging.error(f"❌ Turna satın alma hatası: {e}")
        return render_template("error.html", message="Satın alma işlemi başarısız oldu.")


if __name__ == "__main__":
    app.run()