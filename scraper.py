import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logging.basicConfig(level=logging.INFO)


def get_flights_enuygun_playwright(kalkis, varis, kalkis_kodu, varis_kodu, tarih):
    url = f"https://www.enuygun.com/ucak-bileti/arama/{kalkis}-{varis}-{kalkis_kodu}-{varis_kodu}/?gidis={tarih}&yetiskin=1&sinif=ekonomi"
    flights = []
    try:
        with sync_playwright() as p:
            # Chromium tarayıcısını headless modda başlatıyoruz.
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            page.goto(url, timeout=60000)
            logging.info(f"✅ Enuygun sayfası açıldı: {url}")

            # Belirtilen elementin sayfada görünmesini bekliyoruz.
            page.wait_for_selector(".ticket-card", timeout=60000)
            cards = page.query_selector_all(".ticket-card")

            if not cards:
                logging.error("❌ Enuygun'da uçuş bilgileri bulunamadı!")
                return []

            logging.info(f"✅ {len(cards)} uçuş bulundu.")

            for card in cards:
                try:
                    # Element locator’larını, sitenin güncel HTML yapısına göre güncelleyin.
                    airline_elem = card.query_selector("span.airline-name")
                    price_elem = card.query_selector("span.price")
                    departure_elem = card.query_selector("span.departure-time")

                    if airline_elem and price_elem and departure_elem:
                        airline = airline_elem.inner_text().strip()
                        price = price_elem.inner_text().strip()
                        departure_time = departure_elem.inner_text().strip()

                        flights.append({
                            "kaynak": "Enuygun",
                            "havayolu": airline,
                            "fiyat": price,
                            "kalkış_saati": departure_time
                        })
                except Exception as e:
                    logging.warning(f"⚠️ Bir uçuş bilgisi alınırken hata: {e}")
            browser.close()
    except PlaywrightTimeoutError as e:
        logging.error(f"❌ Enuygun sayfası zaman aşımına uğradı: {e}")
    except Exception as e:
        logging.error(f"❌ Enuygun'dan veri çekerken hata oluştu: {e}")
    return flights


# Diğer siteler için benzer fonksiyonlar oluşturabilirsiniz.
def get_flights_obilet_playwright(kalkis, varis, tarih):
    # Örnek: Obilet için URL ve scraping işlemi.
    url = f"https://www.obilet.com/ucuslar/{kalkis}_4-{varis}_18/{tarih}/1a/economy/all"
    flights = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            page.goto(url, timeout=60000)
            logging.info(f"✅ Obilet sayfası açıldı: {url}")
            page.wait_for_selector(".flight-card", timeout=60000)
            cards = page.query_selector_all(".flight-card")
            if not cards:
                logging.error("❌ Obilet'te uçuş bilgileri bulunamadı!")
                return []
            logging.info(f"✅ {len(cards)} uçuş bulundu.")
            for card in cards:
                try:
                    airline_elem = card.query_selector("span.airline-name")
                    price_elem = card.query_selector("span.price")
                    departure_elem = card.query_selector("span.departure-time")
                    if airline_elem and price_elem and departure_elem:
                        airline = airline_elem.inner_text().strip()
                        price = price_elem.inner_text().strip()
                        departure_time = departure_elem.inner_text().strip()
                        flights.append({
                            "kaynak": "Obilet",
                            "havayolu": airline,
                            "fiyat": price,
                            "kalkış_saati": departure_time
                        })
                except Exception as e:
                    logging.warning(f"⚠️ Obilet uçuş bilgisi alınırken hata: {e}")
            browser.close()
    except Exception as e:
        logging.error(f"❌ Obilet'ten veri çekerken hata oluştu: {e}")
    return flights


def get_flights_turna_playwright(kalkis, varis, tarih):
    # Örnek: Turna için URL ve scraping işlemi.
    url = f"https://www.turna.com/ucak-bileti/{kalkis}-{varis}/{tarih}/{tarih}"
    flights = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            page.goto(url, timeout=60000)
            logging.info(f"✅ Turna sayfası açıldı: {url}")
            page.wait_for_selector(".ticket-card", timeout=60000)
            cards = page.query_selector_all(".ticket-card")
            if not cards:
                logging.error("❌ Turna'da uçuş bilgileri bulunamadı!")
                return []
            logging.info(f"✅ {len(cards)} uçuş bulundu (Turna).")
            for card in cards:
                try:
                    airline_elem = card.query_selector("span.airline-name")
                    price_elem = card.query_selector("span.price")
                    departure_elem = card.query_selector("span.departure-time")
                    if airline_elem and price_elem and departure_elem:
                        airline = airline_elem.inner_text().strip()
                        price = price_elem.inner_text().strip()
                        departure_time = departure_elem.inner_text().strip()
                        flights.append({
                            "kaynak": "Turna",
                            "havayolu": airline,
                            "fiyat": price,
                            "kalkış_saati": departure_time
                        })
                except Exception as e:
                    logging.warning(f"⚠️ Turna uçuş bilgisi alınırken hata: {e}")
            browser.close()
    except Exception as e:
        logging.error(f"❌ Turna.com'dan veri çekerken hata oluştu: {e}")
    return flights