import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logging.basicConfig(level=logging.INFO)


def get_flights_enuygun_playwright(kalkis, varis, kalkis_kodu, varis_kodu, tarih):
    url = f"https://www.enuygun.com/ucak-bileti/arama/{kalkis}-{varis}-{kalkis_kodu}-{varis_kodu}/?gidis={tarih}&yetiskin=1&sinif=ekonomi"
    flights = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            page.goto(url, timeout=60000)
            logging.info(f"✅ Enuygun sayfası açıldı: {url}")

            # Yeni HTML yapısına göre uçuş kartlarını ".flight-item" ile çekiyoruz.
            page.wait_for_selector(".flight-item", timeout=60000)
            cards = page.query_selector_all(".flight-item")

            if not cards:
                logging.error("❌ Enuygun'da uçuş bilgileri bulunamadı!")
                return []

            logging.info(f"✅ {len(cards)} uçuş bulundu.")
            for card in cards:
                try:
                    flight_id = card.get_attribute("data-flight-id")

                    # "flight-summary" container'ı altındaki bilgileri çekiyoruz.
                    summary_wrapper = card.query_selector(".flight-summary")

                    airline = None
                    promo = None
                    departure_time = None
                    price = None

                    if summary_wrapper:
                        airline_elem = summary_wrapper.query_selector(".flight-summary-airline")
                        if airline_elem:
                            airline = airline_elem.inner_text().strip()
                        promo_elem = summary_wrapper.query_selector(".flight-summary-promo")
                        if promo_elem:
                            promo = promo_elem.inner_text().strip()
                        time_elem = summary_wrapper.query_selector(".flight-summary-time")
                        if time_elem:
                            departure_time = time_elem.inner_text().strip()
                        price_elem = summary_wrapper.query_selector(".flight-summary-price")
                        if price_elem:
                            price = price_elem.inner_text().strip()

                    flights.append({
                        "kaynak": "Enuygun",
                        "flight_id": flight_id,
                        "airline": airline,
                        "promo": promo,
                        "departure_time": departure_time,
                        "price": price
                    })
                except Exception as e:
                    logging.warning(f"⚠️ Enuygun uçuş bilgisi alınırken hata: {e}")
            browser.close()
    except PlaywrightTimeoutError as e:
        logging.error(f"❌ Enuygun sayfası zaman aşımına uğradı: {e}")
    except Exception as e:
        logging.error(f"❌ Enuygun'dan veri çekerken hata oluştu: {e}")
    return flights


def get_flights_obilet_playwright(kalkis, varis, tarih):
    # Örnek URL; kalkis ve varis parametreleri genellikle ID şeklinde veriliyor.
    url = f"https://www.obilet.com/ucuslar/{kalkis}_4-{varis}_18/{tarih}/1a/economy/all"
    flights = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            page.goto(url, timeout=60000)
            logging.info(f"✅ Obilet sayfası açıldı: {url}")
            # Obilet için uçuş kartları "#outbound-journeys" altında li.item.journey şeklinde
            page.wait_for_selector("#outbound-journeys li.item.journey", timeout=60000)
            cards = page.query_selector_all("#outbound-journeys li.item.journey")
            if not cards:
                logging.error("❌ Obilet'te uçuş bilgileri bulunamadı!")
                return []
            logging.info(f"✅ {len(cards)} uçuş bulundu.")
            for card in cards:
                try:
                    flight_id = card.get_attribute("data-id")
                    airline_elem = card.query_selector("div.airlines.col")
                    airline = airline_elem.inner_text().strip() if airline_elem else "Bilinmiyor"
                    price_elem = card.query_selector("div.price.col")
                    price = price_elem.inner_text().strip() if price_elem else "Bilinmiyor"
                    time_elem = card.query_selector("div.time.col.row div.left.col")
                    departure_time = time_elem.inner_text().strip() if time_elem else "Bilinmiyor"
                    flights.append({
                        "kaynak": "Obilet",
                        "flight_id": flight_id,
                        "havayolu": airline,
                        "fiyat": price,
                        "kalkış_saati": departure_time
                    })
                except Exception as e:
                    logging.warning(f"⚠️ Obilet uçuş bilgisi alınırken hata: {e}")
            browser.close()
    except PlaywrightTimeoutError as e:
        logging.error(f"❌ Obilet sayfası zaman aşımına uğradı: {e}")
    except Exception as e:
        logging.error(f"❌ Obilet'ten veri çekerken hata oluştu: {e}")
    return flights


def get_flights_turna_playwright(kalkis, varis, tarih):
    url = f"https://www.turna.com/ucak-bileti/{kalkis}-{varis}/{tarih}/{tarih}"
    flights = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            page.goto(url, timeout=60000)
            logging.info(f"✅ Turna sayfası açıldı: {url}")
            # Turna'da uçuş kartları ".flight-card-wrapper_container" ile belirtilmiş
            page.wait_for_selector(".flight-card-wrapper_container", timeout=60000)
            cards = page.query_selector_all(".flight-card-wrapper_container")
            if not cards:
                logging.error("❌ Turna'da uçuş bilgileri bulunamadı!")
                return []
            logging.info(f"✅ {len(cards)} uçuş bulundu (Turna).")
            for card in cards:
                try:
                    content_elem = card.query_selector(".flight-card-wrapper__item_content")
                    summary = content_elem.inner_text().strip() if content_elem else "Bilinmiyor"
                    flights.append({
                        "kaynak": "Turna",
                        "ozet": summary
                    })
                except Exception as e:
                    logging.warning(f"⚠️ Turna uçuş bilgisi alınırken hata: {e}")
            browser.close()
    except PlaywrightTimeoutError as e:
        logging.error(f"❌ Turna sayfası zaman aşımına uğradı: {e}")
    except Exception as e:
        logging.error(f"❌ Turna.com'dan veri çekerken hata oluştu: {e}")
    return flights