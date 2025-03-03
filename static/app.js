document.getElementById("fetchFlights").addEventListener("click", async function() {
  const loader = document.getElementById("loader");
  const flightResults = document.getElementById("flightResults");

  loader.classList.remove("d-none");
  flightResults.innerHTML = "";

  const originSelect = document.getElementById("originSelect");
  const destinationSelect = document.getElementById("destinationSelect");
  const travelDate = document.getElementById("travelDate").value;

  const kalkis = originSelect.value;
  const kalkis_kodu = originSelect.options[originSelect.selectedIndex].dataset.code;
  const varis = destinationSelect.value;
  const varis_kodu = destinationSelect.options[destinationSelect.selectedIndex].dataset.code || "";

  const apiUrl = `/api/flights?kalkis=${encodeURIComponent(kalkis)}&varis=${encodeURIComponent(varis)}&kalkis_kodu=${encodeURIComponent(kalkis_kodu)}&varis_kodu=${encodeURIComponent(varis_kodu)}&tarih=${encodeURIComponent(travelDate)}`;

  try {
    let response = await fetch(apiUrl);
    let data = await response.json();
    if (data.error) {
      flightResults.innerHTML = `<p>${data.error}: ${data.details}</p>`;
      return;
    }

    let html = "";

    let enuygunFlights = data.filter(flight => flight.kaynak === "Enuygun");
    if (enuygunFlights.length > 0) {
      html += `
        <h3>Enuygun Uçuşları</h3>
        <div class="col-12">
          <table class="table table-hover">
            <thead class="table-primary">
              <tr>
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
        let route = `${originSelect.options[originSelect.selectedIndex].text} → ${destinationSelect.options[destinationSelect.selectedIndex].text}`;
        html += `
          <tr data-price="${flight.price}">
            <td>${flight.airline || "Bilinmiyor"}</td>
            <td>${route}</td>
            <td>${flight.departure_time || "Bilinmiyor"}</td>
            <td>${flight.price || "Bilinmiyor"}</td>
            <td>
              <button class="buy-btn btn btn-success" 
                      onclick="purchaseEnuygun(this)" 
                      data-purchase-url="${flight.purchase_url || ''}"
                      data-flight-id="${flight.flight_id || ''}"
                      data-request-id="${flight.request_id || ''}"
                      data-final-purchase-url="${flight.final_purchase_url || ''}">
                Satın Al
              </button>
            </td>
          </tr>
        `;
      });
      html += `
            </tbody>
          </table>
        </div>
      `;
    } else {
      html += "<h3>Enuygun Uçuşları</h3><p>Hiç uçuş bulunamadı.</p>";
    }

    let turnaFlights = data.filter(flight => flight.kaynak === "Turna" && flight.tripType === "oneway");
    if (turnaFlights.length > 0) {
      html += `
        <h3>Turna Tek Yön Uçuşları</h3>
        <div class="col-12">
          <table class="table table-hover">
            <thead class="table-primary">
              <tr>
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
      turnaFlights.forEach(flight => {
        let route = `${originSelect.options[originSelect.selectedIndex].text} → ${destinationSelect.options[destinationSelect.selectedIndex].text}`;
        html += `
          <tr data-price="${flight.price}">
            <td>${flight.airline || "Bilinmiyor"}</td>
            <td>${route}</td>
            <td>${flight.departure_time || "Bilinmiyor"}</td>
            <td>${flight.arrival_time || "Bilinmiyor"}</td>
            <td>${flight.duration || "Bilinmiyor"}</td>
            <td>${flight.price || "Bilinmiyor"}</td>
            <td>
              <button class="buy-btn btn btn-success" 
                      onclick="purchaseTurna(this)" 
                      data-purchase-url="${flight.purchase_url || ''}"
                      data-flight-id="${flight.flight_id || ''}"
                      data-final-purchase-url="${flight.final_purchase_url || ''}">
                Satın Al
              </button>
            </td>
          </tr>
        `;
      });
      html += `
            </tbody>
          </table>
        </div>
      `;
    } else {
      html += "<h3>Turna Tek Yön Uçuşları</h3><p>Hiç uçuş bulunamadı.</p>";
    }

    flightResults.innerHTML = html;
  } catch (error) {
    console.error("Hata:", error);
    flightResults.innerHTML = "<p>Bir hata oluştu. Lütfen tekrar deneyin.</p>";
  } finally {
    loader.classList.add("d-none");
  }
});

async function purchaseEnuygun(button) {
  const finalUrl = button.getAttribute("data-final-purchase-url");
  if (finalUrl && finalUrl.trim() !== "") {
    window.open(finalUrl, '_blank');
    return;
  }
  const purchaseUrl = button.getAttribute("data-purchase-url");
  const flightId = button.getAttribute("data-flight-id");
  const requestId = button.getAttribute("data-request-id");
  if (purchaseUrl && purchaseUrl.trim() !== "") {
    alert("Satın alma işlemi başlatılıyor. Lütfen bekleyin...");
    try {
      const response = await fetch(`/purchase/enuygun?flight_id=${encodeURIComponent(flightId)}&request_id=${encodeURIComponent(requestId)}`);
      if (response.ok) {
        const data = await response.json();
        if (data.final_url) {
          window.open(data.final_url, '_blank');
        } else {
          alert("Satın alma işlemi başarısız oldu. Lütfen tekrar deneyin.");
        }
      } else {
        alert("Satın alma işlemi sırasında bir hata oluştu.");
      }
    } catch (error) {
      console.error("Hata:", error);
      alert("Satın alma işlemi sırasında bir hata oluştu.");
    }
  } else {
    alert("Satın alma linki bulunamadı.");
  }
}

function purchaseTurna(button) {
  const finalUrl = button.getAttribute("data-final-purchase-url");
  if (finalUrl && finalUrl.trim() !== "") {
    window.open(finalUrl, '_blank');
    return;
  }
  const purchaseUrl = button.getAttribute("data-purchase-url");
  // Artık purchaseUrl scraper tarafından "flight_id" parametresiyle oluşturuluyor,
  // bu yüzden ek bir query string eklemeye gerek yok.
  if (purchaseUrl && purchaseUrl.trim() !== "") {
    alert("Satın alma işlemi başlatılıyor. Lütfen bekleyin...");
    window.open(purchaseUrl, '_blank');
    window.close();
  } else {
    alert("Satın alma linki bulunamadı.");
  }
}