import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logging.basicConfig(level=logging.INFO)


def format_date_for_enuygun(date_str):
    # date_str "2025-02-28" formatında geliyorsa, "28.02.2025" formatına çevirir.
    try:
        parts = date_str.split('-')
        if len(parts) == 3:
            return f"{parts[2]}.{parts[1]}.{parts[0]}"
        return date_str
    except Exception:
        return date_str


def get_flights_enuygun_playwright(kalkis, varis, kalkis_kodu, varis_kodu, tarih):
    # Tarihi doğru formatta eklemek için
    gidis_tarih = format_date_for_enuygun(tarih)
    url = (f"https://www.enuygun.com/ucak-bileti/arama/"
           f"{kalkis}-{varis}-{kalkis_kodu}-{varis_kodu}/"
           f"?gidis={gidis_tarih}&yetiskin=1&sinif=ekonomi&trip=domestic&geotrip=domestic&market=tr&language=tr")
    flights = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            page.goto(url, timeout=60000)
            logging.info(f"✅ Enuygun sayfası açıldı: {url}")

            page.wait_for_selector(".flight-item", timeout=60000)
            cards = page.query_selector_all(".flight-item")
            if not cards:
                logging.error("❌ Enuygun'da uçuş bilgileri bulunamadı!")
                return []
            logging.info(f"✅ {len(cards)} uçuş bulundu.")
            for card in cards:
                try:
                    flight_id = card.get_attribute("data-flight-id")
                    request_id = card.get_attribute("data-request-id")

                    summary_wrapper = card.query_selector(".flight-summary")
                    airline = promo = departure_time = price = None
                    if summary_wrapper:
                        airline_elem = summary_wrapper.query_selector(".flight-summary-airline")
                        promo_elem = summary_wrapper.query_selector(".flight-summary-promo")
                        time_elem = summary_wrapper.query_selector(".flight-summary-time")
                        price_elem = summary_wrapper.query_selector(".flight-summary-price .summary-average-price")
                        airline = airline_elem.inner_text().strip() if airline_elem else None
                        promo = promo_elem.inner_text().strip() if promo_elem else None
                        departure_time = time_elem.inner_text().strip() if time_elem else None
                        price = price_elem.get_attribute("data-price") if price_elem else None

                    # Eğer uçuş kartında origin/destination bilgisi yoksa, form verileri kullanılır.
                    origin_elem = card.query_selector(".segment-airport-origin")
                    origin = origin_elem.inner_text().strip() if origin_elem else kalkis
                    destination_elem = card.query_selector(".segment-airport-destination")
                    destination = None
                    if destination_elem:
                        dest_name_elem = destination_elem.query_selector(".combineAirportName")
                        if dest_name_elem:
                            destination = dest_name_elem.get_attribute("title")
                            if destination:
                                destination = destination.strip()
                        if not destination:
                            destination = destination_elem.inner_text().strip()
                    if not destination:
                        destination = varis

                    terminal_elem = card.query_selector(".segment-airport-terminal")
                    terminal = terminal_elem.inner_text().strip() if terminal_elem else None

                    warnings_elem = card.query_selector(".segment-warnings")
                    warnings_text = warnings_elem.inner_text().strip() if warnings_elem else None

                    attributes_elem = card.query_selector('[data-testid="airlineInfoWrapper"]')
                    attributes = attributes_elem.inner_text().strip() if attributes_elem else None

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
                        "terminal": terminal,
                        "warnings": warnings_text,
                        "attributes": attributes
                    })
                except Exception as e:
                    logging.warning(f"⚠️ Enuygun uçuş bilgisi alınırken hata: {e}")
            browser.close()
    except PlaywrightTimeoutError as e:
        logging.error(f"❌ Enuygun sayfası zaman aşımına uğradı: {e}")
    except Exception as e:
        logging.error(f"❌ Enuygun'dan veri çekerken hata oluştu: {e}")
    return flights

def get_flights_turna_oneway_playwright(kalkis, varis, tarih):
    """
    Turna.com için tek yön uçuş verilerini çeker.
    Örnek URL: https://www.turna.com/ucak-bileti/{kalkis}-{varis}/{tarih}
    """
    url = f"https://www.turna.com/ucak-bileti/{kalkis}-{varis}/{tarih}"
    flights = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            page.goto(url, timeout=60000)
            logging.info(f"✅ Turna tek yön sayfası açıldı: {url}")

            page.wait_for_selector(".flight-card-wrapper__item", timeout=60000)
            cards = page.query_selector_all(".flight-card-wrapper__item")
            if not cards:
                logging.error("❌ Turna tek yön uçuşları bulunamadı!")
                return []
            logging.info(f"✅ {len(cards)} tek yön uçuş bulundu (Turna).")
            for card in cards:
                try:
                    # Flight ID: Kartın id attribute'si ya da benzersiz bir placeholder
                    flight_id = card.get_attribute("id")
                    if not flight_id:
                        flight_id = "turna-" + str(hash(card.inner_text()))

                    airline_elem = card.query_selector(".airline-name")
                    airline = airline_elem.inner_text().strip() if airline_elem else None

                    origin_elem = card.query_selector("span.origin")
                    destination_elem = card.query_selector("span.destination")
                    origin = origin_elem.inner_text().strip() if origin_elem else None
                    destination = destination_elem.inner_text().strip() if destination_elem else None
                    if not origin or not destination:
                        origin = kalkis
                        destination = varis

                    dep_elem = card.query_selector(".departure-date")
                    arr_elem = card.query_selector(".arrival-date")
                    departure_time = dep_elem.inner_text().strip() if dep_elem else None
                    arrival_time = arr_elem.inner_text().strip() if arr_elem else None

                    duration_elem = card.query_selector(".duration")
                    duration = duration_elem.inner_text().strip() if duration_elem else None

                    price_elem = card.query_selector(".money-val")
                    price = price_elem.inner_text().strip() if price_elem else None

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
                        "tripType": "oneway"
                    })
                except Exception as e:
                    logging.warning(f"⚠️ Turna tek yön uçuş bilgisi alınırken hata: {e}")
            browser.close()
    except PlaywrightTimeoutError as e:
        logging.error(f"❌ Turna tek yön sayfası zaman aşımına uğradı: {e}")
    except Exception as e:
        logging.error(f"❌ Turna tek yön uçuş verisi çekilirken hata: {e}")
    return flights