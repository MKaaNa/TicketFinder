from flask import Flask, jsonify, render_template, request, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from urllib.parse import quote
from scraper import get_flights_enuygun_playwright, get_flights_turna_oneway_playwright

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.config["DEBUG"] = True

limiter = Limiter(get_remote_address, app=app, default_limits=["2 per second"])


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/flights", methods=["GET"])
def flights():
    # Kullanıcı formundan gelen değerler
    kalkis = request.args.get("kalkis", "ankara-esenboga-havalimani")
    varis = request.args.get("varis", "istanbul-sabiha-gokcen-havalimani")
    kalkis_kodu = request.args.get("kalkis_kodu", "esb")
    varis_kodu = request.args.get("varis_kodu", "saw")
    tarih = request.args.get("tarih", "2025-02-28")

    logging.info(f"🔍 Arama: {kalkis} ({kalkis_kodu}) → {varis} ({varis_kodu}) | Tarih: {tarih}")

    try:
        enuygun = get_flights_enuygun_playwright(kalkis, varis, kalkis_kodu, varis_kodu, tarih)
        turna = get_flights_turna_oneway_playwright(kalkis, varis, tarih)
        # Sadece Enuygun ve Turna verileri döndürülüyor
        all_flights = enuygun + turna
        return jsonify(all_flights)
    except Exception as e:
        logging.error(f"Uçuş verileri alınırken hata oluştu: {e}")
        return jsonify({"error": "Uçuş verileri alınırken hata oluştu", "details": str(e)}), 500


@app.route("/purchase", methods=["GET"])
def purchase():
    flight_id = request.args.get("flight_id")
    source = request.args.get("source")
    if source == "Enuygun":
        request_id = request.args.get("request_id")
        baseUrl = "https://www.enuygun.com/ucak-bileti/rezervasyon/?trip=domestic&geotrip=domestic&is_lc=0&route_type=one-way"
        if flight_id:
            if request_id and request_id.strip():
                return redirect(f"{baseUrl}&request_id={quote(request_id)}&flight_id={quote(flight_id)}")
            else:
                return redirect(f"{baseUrl}&flight_id={quote(flight_id)}")
        else:
            return redirect(f"{baseUrl}&request_id=default")
    elif source == "Turna":
        if flight_id:
            return redirect(f"https://www.turna.com/ucak-bileti/rezervasyon/?flight_id={quote(flight_id)}")
        else:
            return redirect("https://www.turna.com/ucak-bileti/rezervasyon/")
    else:
        return "Bilet satışı için uygun kaynak bulunamadı.", 400


if __name__ == "__main__":
    app.run()