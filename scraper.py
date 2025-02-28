import logging
import random
import time
import uuid
import traceback
from urllib.parse import quote
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logging.basicConfig(level=logging.INFO)


# Hata sınıfları
class ScraperError(Exception):
    """Tüm scraping hataları için base class"""


class FlightIDNotFoundError(ScraperError):
    """Flight ID bulunamadığında fırlatılır"""


def generate_request_id():
    return str(uuid.uuid4())


def format_date_for_enuygun(date_str):
    # YYYY-MM-DD -> DD.MM.YYYY
    try:
        parts = date_str.split('-')
        if len(parts) == 3:
            return f"{parts[2]}.{parts[1]}.{parts[0]}"
        return date_str
    except Exception:
        return date_str


def extract_turna_flight_id(card):
    flight_id = card.get_attribute("data-flight-id")
    if not flight_id:
        link_elem = card.query_selector("a[href*='/rezervasyon/']")
        if link_elem:
            href = link_elem.get_attribute("href")
            if href:
                flight_id = href.split("/")[-1]
    if not flight_id:
        flight_id = f"turna-{hash(card.inner_text())}"
    return flight_id


def get_flights_enuygun_playwright(kalkis, varis, kalkis_kodu, varis_kodu, tarih):
    gidis_tarih = format_date_for_enuygun(tarih)
    url = (
        f"https://www.enuygun.com/ucak-bileti/arama/"
        f"{kalkis}-{varis}-{kalkis_kodu}-{varis_kodu}/"
        f"?gidis={gidis_tarih}&yetiskin=1&sinif=ekonomi&trip=domestic&geotrip=domestic&market=tr&language=tr"
    )
    flights = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                ignore_https_errors=True,
                user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"),
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()
            page.goto(url, timeout=60000)
            logging.info(f"✅ Enuygun sayfası açıldı: {url}")
            time.sleep(random.uniform(1, 3))
            page.wait_for_selector(".flight-item", timeout=60000)
            cards = page.query_selector_all(".flight-item")
            if not cards:
                logging.error("❌ Enuygun'da uçuş bilgileri bulunamadı!")
                return []
            logging.info(f"✅ {len(cards)} uçuş bulundu (Enuygun).")
            for card in cards:
                try:
                    flight_id = card.get_attribute("data-flight-id")
                    if not flight_id:
                        raise FlightIDNotFoundError("Enuygun uçuş kartında flight ID bulunamadı!")
                    request_id = card.get_attribute("data-request-id") or generate_request_id()

                    summary_wrapper = card.query_selector(".flight-summary")
                    airline = promo = departure_time = price = None
                    if summary_wrapper:
                        airline_elem = summary_wrapper.query_selector(".flight-summary-airline")
                        promo_elem = summary_wrapper.query_selector(".flight-summary-promo")
                        time_elem = summary_wrapper.query_selector(".flight-summary-time")
                        price_elem = summary_wrapper.query_selector(".flight-summary-price .summary-average-price")
                        airline = airline_elem.inner_text().strip() if airline_elem else "Bilinmiyor"
                        promo = promo_elem.inner_text().strip() if promo_elem else ""
                        departure_time = time_elem.inner_text().strip() if time_elem else "Bilinmiyor"
                        if price_elem:
                            price = price_elem.get_attribute("data-price")
                            if not price or price.strip() == "":
                                price = price_elem.inner_text().strip()
                        else:
                            price = "Bilinmiyor"

                    origin = kalkis
                    destination = varis

                    purchase_url = f"/purchase/enuygun?flight_id={quote(flight_id)}&request_id={quote(request_id)}"

                    flights.append({
                        "kaynak": "Enuygun",
                        "flight_id": flight_id,
                        "request_id": request_id,
                        "airline": airline,
                        "promo": promo,
                        "departure_time": departure_time,
                        "price": price,
                        "origin": origin,
                        "destination": destination,
                        "purchase_url": purchase_url,
                        "final_purchase_url": ""
                    })
                except Exception as inner_e:
                    logging.warning(f"⚠️ Enuygun uçuş bilgisi alınırken hata: {traceback.format_exc()}")
            browser.close()
        return flights
    except PlaywrightTimeoutError as te:
        logging.error(f"❌ Enuygun sayfası zaman aşımına uğradı: {str(te)}", exc_info=True)
        raise
    except Exception as e:
        logging.critical(f"❌ Enuygun'dan veri çekerken beklenmeyen hata: {traceback.format_exc()}")
        raise


def get_flights_turna_oneway_playwright(kalkis, varis, tarih):
    url = f"https://www.turna.com/ucak-bileti/{kalkis}-{varis}/{tarih}"
    flights = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                ignore_https_errors=True,
                user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"),
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()
            page.goto(url, timeout=60000)
            logging.info(f"✅ Turna tek yön sayfası açıldı: {url}")
            time.sleep(random.uniform(1, 3))
            page.wait_for_selector(".flight-card-wrapper__item", timeout=60000)
            cards = page.query_selector_all(".flight-card-wrapper__item")
            if not cards:
                logging.error("❌ Turna tek yön uçuşları bulunamadı!")
                return []
            logging.info(f"✅ {len(cards)} tek yön uçuş bulundu (Turna).")
            for card in cards:
                try:
                    flight_id = extract_turna_flight_id(card)
                    airline_elem = card.query_selector(".airline-name")
                    airline = airline_elem.inner_text().strip() if airline_elem else "Bilinmiyor"
                    origin_elem = card.query_selector("span.origin")
                    destination_elem = card.query_selector("span.destination")
                    origin = origin_elem.inner_text().strip() if origin_elem else kalkis
                    destination = destination_elem.inner_text().strip() if destination_elem else varis
                    dep_elem = card.query_selector(".departure-date")
                    arr_elem = card.query_selector(".arrival-date")
                    departure_time = dep_elem.inner_text().strip() if dep_elem else "Bilinmiyor"
                    arrival_time = arr_elem.inner_text().strip() if arr_elem else "Bilinmiyor"
                    duration_elem = card.query_selector(".duration")
                    duration = duration_elem.inner_text().strip() if duration_elem else "Bilinmiyor"
                    price_elem = card.query_selector(".money-val")
                    price = price_elem.inner_text().strip() if price_elem else "Bilinmiyor"

                    base_purchase_url = "/purchase/turna"
                    purchase_url = f"{base_purchase_url}?flight_id={quote(flight_id)}"

                    flights.append({
                        "kaynak": "Turna",
                        "flight_id": flight_id,
                        "airline": airline,
                        "origin": origin,
                        "destination": destination,
                        "departure_time": departure_time,
                        "arrival_time": arrival_time,
                        "duration": duration,
                        "price": price,
                        "tripType": "oneway",
                        "purchase_url": purchase_url,
                        "final_purchase_url": ""
                    })
                except Exception as inner_e:
                    logging.warning(f"⚠️ Turna uçuş bilgisi alınırken hata: {traceback.format_exc()}")
            browser.close()
        return flights
    except PlaywrightTimeoutError as te:
        logging.error(f"❌ Turna tek yön sayfası zaman aşımına uğradı: {str(te)}", exc_info=True)
        raise
    except Exception as e:
        logging.critical(f"❌ Turna uçuş verisi çekilirken beklenmeyen hata: {traceback.format_exc()}")
        raise


def simulate_purchase_enuygun(flight_id, request_id):
    if not request_id or request_id.strip() == "":
        request_id = generate_request_id()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                ignore_https_errors=True,
                user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"),
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()
            purchase_url = (
                f"https://www.enuygun.com/ucak-bileti/rezervasyon/"
                f"?request_id={request_id}&trip=domestic&geotrip=domestic&is_lc=0&route_type=one-way&flight_id={quote(flight_id)}"
            )
            page.goto(purchase_url, timeout=120000)
            logging.info(f"✅ Enuygun satın alma sayfası açıldı: {purchase_url}")
            page.wait_for_load_state("networkidle", timeout=120000)
            time.sleep(random.uniform(2, 4))
            try:
                page.wait_for_selector(".action-select-btn:visible", timeout=80000)
                select_btn = page.query_selector(".action-select-btn")
                if select_btn:
                    select_btn.click()
                    logging.info("✅ 'Seç' butonuna tıklandı.")
                else:
                    logging.warning("⚠️ 'Seç' butonu bulunamadı.")
            except Exception as wait_err:
                logging.error(f"❌ 'Seç' butonuyla ilgili hata: {wait_err}")
            time.sleep(random.uniform(2, 4))
            try:
                page.wait_for_selector('[data-testid="providerSelectBtn"]:visible', timeout=80000)
                ilerle_btn = page.query_selector('[data-testid="providerSelectBtn"]')
                if ilerle_btn:
                    page.evaluate("element => element.scrollIntoView({behavior: 'smooth', block: 'center'})",
                                  ilerle_btn)
                    page.hover('[data-testid="providerSelectBtn"]')
                    time.sleep(random.uniform(1, 2))
                    ilerle_btn.click()
                    logging.info("✅ 'Seç ve İlerle' butonuna tıklandı.")
                    page.wait_for_url("**/odeme/**", timeout=120000)
                else:
                    logging.warning("⚠️ 'Seç ve İlerle' butonu bulunamadı; mevcut URL kullanılacak.")
            except Exception as wait_err:
                logging.error(f"❌ 'Seç ve İlerle' butonuyla ilgili hata: {wait_err}")
            final_url = page.url
            logging.info(f"✅ Enuygun son satın alma URL'si: {final_url}")
            browser.close()
            return final_url
    except Exception as e:
        logging.error(f"❌ Enuygun satın alma akışı sırasında hata: {e}")
        return purchase_url


def simulate_purchase_turna(flight_id):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                ignore_https_errors=True,
                user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"),
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()
            purchase_url = f"https://www.turna.com/ucak-bileti/rezervasyon/{quote(flight_id)}"
            page.goto(purchase_url, timeout=60000)
            logging.info(f"✅ Turna satın alma sayfası açıldı: {purchase_url}")
            page.wait_for_load_state("networkidle", timeout=80000)
            final_url = page.url
            logging.info(f"✅ Turna son satın alma URL'si: {final_url}")
            browser.close()
            return final_url
    except Exception as e:
        logging.error(f"❌ Turna satın alma akışı sırasında hata: {e}")
        return purchase_url