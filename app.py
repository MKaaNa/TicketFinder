from flask import Flask, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from scraper import get_flights_enuygun_playwright, get_flights_obilet_playwright, \
    get_flights_turna_playwright

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.config["DEBUG"] = True

limiter = Limiter(get_remote_address, app=app, default_limits=["2 per second"])


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/flights", methods=["GET"])
@limiter.limit("2 per second")
def flights():
    kalkis = request.args.get("kalkis", "ankara-esenboga-havalimani")
    varis = request.args.get("varis", "istanbul-sabiha-gokcen-havalimani")
    kalkis_kodu = request.args.get("kalkis_kodu", "esb")
    varis_kodu = request.args.get("varis_kodu", "saw")
    tarih = request.args.get("tarih", "2025-02-27")

    logging.info(f"🔍 {kalkis} ({kalkis_kodu}) → {varis} ({varis_kodu}) | Tarih: {tarih}")

    try:
        enuygun = get_flights_enuygun_playwright(kalkis, varis, kalkis_kodu, varis_kodu, tarih)
        obilet = get_flights_obilet_playwright("222", "251", tarih)
        turna = get_flights_turna_playwright(kalkis, varis, tarih)
        all_flights = enuygun + obilet + turna
        return jsonify(all_flights)
    except Exception as e:
        logging.error(f"Uçuş verileri alınırken hata oluştu: {e}")
        return jsonify({"error": "Uçuş verileri alınırken hata oluştu", "details": str(e)}), 500


if __name__ == "__main__":
    app.run()