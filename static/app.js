document.getElementById("fetchFlights").addEventListener("click", async function() {
  const loader = document.getElementById("loader");
  const flightResults = document.getElementById("flightResults");
  const turnaOnewaySection = document.getElementById("turnaOnewaySection");

  loader.style.display = "block";
  flightResults.innerHTML = "";
  turnaOnewaySection.innerHTML = "";

  // Kullanıcının seçimlerini al
  const originSelect = document.getElementById("originSelect");
  const destinationSelect = document.getElementById("destinationSelect");
  const travelDate = document.getElementById("travelDate").value;

  const kalkis = originSelect.value;
  const kalkis_kodu = originSelect.options[originSelect.selectedIndex].dataset.code;
  const varis = destinationSelect.value;
  const varis_kodu = destinationSelect.options[destinationSelect.selectedIndex].dataset.code || "";

  // API URL'si: Enuygun ve Turna uçuş verilerini getirir.
  const apiUrl = `/api/flights?kalkis=${encodeURIComponent(kalkis)}&varis=${encodeURIComponent(varis)}&kalkis_kodu=${encodeURIComponent(kalkis_kodu)}&varis_kodu=${encodeURIComponent(varis_kodu)}&tarih=${encodeURIComponent(travelDate)}`;

  try {
    let response = await fetch(apiUrl);
    let data = await response.json();
    if (data.error) {
      flightResults.innerHTML = `<p>${data.error}: ${data.details}</p>`;
      return;
    }

    // Enuygun uçuşlarını listele
    let enuygunFlights = data.filter(flight => flight.kaynak === "Enuygun");
    let enuygunHtml = "";
    if (enuygunFlights.length > 0) {
      enuygunHtml += `
        <h3>Enuygun Uçuşları</h3>
        <table>
          <thead>
            <tr>
              <th>Uçuş ID</th>
              <th>Havayolu</th>
              <th>Rota</th>
              <th>Kalkış</th>
              <th>Fiyat</th>
              <th>İşlem</th>
            </tr>
          </thead>
          <tbody>
      `;
      enuygunFlights.forEach(flight => {
        let route = (flight.origin && flight.destination)
                    ? (flight.origin + " - " + flight.destination)
                    : (originSelect.options[originSelect.selectedIndex].text + " - " + destinationSelect.options[destinationSelect.selectedIndex].text);
        enuygunHtml += `
          <tr>
            <td>${flight.flight_id || "Bilinmiyor"}</td>
            <td>${flight.airline || "Bilinmiyor"}</td>
            <td>${route}</td>
            <td>${flight.departure_time || "Bilinmiyor"}</td>
            <td>${flight.price || "Bilinmiyor"}</td>
            <td><button class="buy-btn" onclick="buyTicket('${flight.flight_id}', 'Enuygun', '${flight.request_id || ''}')">Satın Al</button></td>
          </tr>
        `;
      });
      enuygunHtml += `
          </tbody>
        </table>
      `;
      flightResults.innerHTML += enuygunHtml;
    } else {
      flightResults.innerHTML += "<h3>Enuygun Uçuşları</h3><p>Hiç uçuş bulunamadı.</p>";
    }

    // Turna tek yön uçuşlarını listele
    let turnaOneWay = data.filter(flight => flight.kaynak === "Turna" && flight.tripType === "oneway");
    let turnaHtml = "";
    if (turnaOneWay.length > 0) {
      turnaHtml += `
        <h3>Turna Tek Yön Uçuşları</h3>
        <table>
          <thead>
            <tr>
              <th>Uçuş ID</th>
              <th>Havayolu</th>
              <th>Rota</th>
              <th>Kalkış</th>
              <th>Varış</th>
              <th>Süre</th>
              <th>Fiyat</th>
              <th>İşlem</th>
            </tr>
          </thead>
          <tbody>
      `;
      turnaOneWay.forEach(flight => {
        let route = (flight.origin && flight.destination)
                    ? (flight.origin + " - " + flight.destination)
                    : (originSelect.options[originSelect.selectedIndex].text + " - " + destinationSelect.options[destinationSelect.selectedIndex].text);
        turnaHtml += `
          <tr>
            <td>${flight.flight_id || "Bilinmiyor"}</td>
            <td>${flight.airline || "Bilinmiyor"}</td>
            <td>${route}</td>
            <td>${flight.departure_time || "Bilinmiyor"}</td>
            <td>${flight.arrival_time || "Bilinmiyor"}</td>
            <td>${flight.duration || "Bilinmiyor"}</td>
            <td>${flight.price || "Bilinmiyor"}</td>
            <td><button class="buy-btn" onclick="buyTicket('${flight.flight_id}', 'Turna')">Satın Al</button></td>
          </tr>
        `;
      });
      turnaHtml += `
          </tbody>
        </table>
      `;
      turnaOnewaySection.innerHTML = turnaHtml;
    } else {
      turnaOnewaySection.innerHTML = "<h3>Turna Tek Yön Uçuşları</h3><p>Hiç uçuş bulunamadı.</p>";
    }

  } catch (error) {
    console.error("Hata:", error);
    flightResults.innerHTML = "<p>Bir hata oluştu. Lütfen tekrar deneyin.</p>";
  } finally {
    loader.style.display = "none";
  }
});

// Satın al butonuna tıklandığında, ilgili uçuşun kendi rezervasyon sayfasına yönlendir.
function buyTicket(flightId, source, requestId) {
  if (source === "Enuygun") {
    let baseUrl = "https://www.enuygun.com/ucak-bileti/rezervasyon/?trip=domestic&geotrip=domestic&is_lc=0&route_type=one-way";
    if (flightId) {
      if (requestId && requestId.trim() !== "") {
        window.location.href = `${baseUrl}&request_id=${encodeURIComponent(requestId)}&flight_id=${encodeURIComponent(flightId)}`;
      } else {
        window.location.href = `${baseUrl}&flight_id=${encodeURIComponent(flightId)}`;
      }
    } else {
      window.location.href = `${baseUrl}&request_id=default`;
    }
  } else if (source === "Turna") {
    if (flightId) {
      window.location.href = `https://www.turna.com/ucak-bileti/rezervasyon/${encodeURIComponent(flightId)}`;
    } else {
      window.location.href = "https://www.turna.com/ucak-bileti/rezervasyon/";
    }
  }
}