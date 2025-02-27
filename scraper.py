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

            # Uçuş kartları, artık ".flight-item" sınıfına sahip
            page.wait_for_selector(".flight-item", timeout=60000)
            cards = page.query_selector_all(".flight-item")
            if not cards:
                logging.error("❌ Enuygun'da uçuş bilgileri bulunamadı!")
                return []
            logging.info(f"✅ {len(cards)} uçuş bulundu.")
            for card in cards:
                try:
                    flight_id = card.get_attribute("data-flight-id")

                    # Özet bilgiler .flight-summary container'ı altında
                    summary_wrapper = card.query_selector(".flight-summary")
                    airline = promo = departure_time = price = None
                    if summary_wrapper:
                        airline_elem = summary_wrapper.query_selector(".flight-summary-airline")
                        promo_elem = summary_wrapper.query_selector(".flight-summary-promo")
                        time_elem = summary_wrapper.query_selector(".flight-summary-time")
                        price_elem = summary_wrapper.query_selector(".flight-summary-price")
                        airline = airline_elem.inner_text().strip() if airline_elem else None
                        promo = promo_elem.inner_text().strip() if promo_elem else None
                        departure_time = time_elem.inner_text().strip() if time_elem else None
                        price = price_elem.inner_text().strip() if price_elem else None

                    # Ek uçuş detayları:
                    origin_elem = card.query_selector(".segment-airport-origin")
                    origin = origin_elem.inner_text().strip() if origin_elem else None

                    destination_elem = card.query_selector(".segment-airport-destination")
                    destination = None
                    if destination_elem:
                        # Örneğin; destination bilgisini title attribute'ü ile almak
                        dest_name_elem = destination_elem.query_selector(".combineAirportName")
                        if dest_name_elem:
                            destination = dest_name_elem.get_attribute("title")
                            if destination:
                                destination = destination.strip()
                        if not destination:
                            destination = destination_elem.inner_text().strip()

                    terminal_elem = card.query_selector(".segment-airport-terminal")
                    terminal = terminal_elem.inner_text().strip() if terminal_elem else None

                    warnings_elem = card.query_selector(".segment-warnings")
                    warnings_text = warnings_elem.inner_text().strip() if warnings_elem else None

                    attributes_elem = card.query_selector('[data-testid="airlineInfoWrapper"]')
                    attributes = attributes_elem.inner_text().strip() if attributes_elem else None

                    flights.append({
                        "kaynak": "Enuygun",
                        "flight_id": flight_id,
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


def get_flights_obilet_playwright(kalkis, varis, tarih):
    url = f"https://www.obilet.com/ucuslar/{kalkis}_4-{varis}_18/{tarih}/1a/economy/all"
    flights = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            page.goto(url, timeout=60000)
            logging.info(f"✅ Obilet sayfası açıldı: {url}")
            # Obilet için uçuş kartları: "#outbound-journeys li.item.journey"
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
                    price_elem = card.query_selector("div.price.col")
                    time_elem = card.query_selector("div.time.col.row div.left.col")

                    airline = airline_elem.inner_text().strip() if airline_elem else None
                    price = price_elem.inner_text().strip() if price_elem else None
                    departure_time = time_elem.inner_text().strip() if time_elem else None

                    flights.append({
                        "kaynak": "Obilet",
                        "flight_id": flight_id,
                        "airline": airline,
                        "price": price,
                        "departure_time": departure_time
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
            # Turna için uçuş kartları, ".flight-card-wrapper_container" yerine ".div-search-list__content" altında olabilir.
            page.wait_for_selector(".div-search-list__content", timeout=60000)
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
                        "summary": summary
                    })
                except Exception as e:
                    logging.warning(f"⚠️ Turna uçuş bilgisi alınırken hata: {e}")
            browser.close()
    except PlaywrightTimeoutError as e:
        logging.error(f"❌ Turna sayfası zaman aşımına uğradı: {e}")
    except Exception as e:
        logging.error(f"❌ Turna.com'dan veri çekerken hata oluştu: {e}")
    return flights