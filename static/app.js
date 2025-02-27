document.getElementById("fetchFlights").addEventListener("click", async function() {
    const loader = document.getElementById("loader");
    const flightResults = document.getElementById("flightResults");
    loader.style.display = "block";
    flightResults.innerHTML = "";

    try {
        let response = await fetch("/api/flights");
        let data = await response.json();
        if (data.error) {
            flightResults.innerHTML = `<p>${data.error}: ${data.details}</p>`;
            return;
        }
        // Örnek olarak, Turna uçuşlarını tablo şeklinde gösterelim
        let turnaFlights = data.filter(flight => flight.kaynak === "Turna");
        let tableHtml = "";
        if (turnaFlights.length > 0) {
            tableHtml += `
                <h3>Turna Uçuşları</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Havayolu</th>
                            <th>Kalkış</th>
                            <th>Varış</th>
                            <th>Süre</th>
                            <th>Fiyat</th>
                            <th>Promosyon</th>
                            <th>İşlem</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            turnaFlights.forEach(flight => {
                tableHtml += `
                    <tr>
                        <td>${flight.airline || "Bilinmiyor"}</td>
                        <td>${flight.departure_time || "Bilinmiyor"} (${flight.departure_code || "?"})</td>
                        <td>${flight.arrival_time || "Bilinmiyor"} (${flight.arrival_code || "?"})</td>
                        <td>${flight.duration || "Bilinmiyor"}</td>
                        <td>${flight.price || "Bilinmiyor"}</td>
                        <td>${flight.promo || "Yok"}</td>
                        <td><button class="buy-btn" onclick="buyTicket('${flight.flight_id || 'turna'}')">Satın Al</button></td>
                    </tr>
                `;
            });
            tableHtml += `
                    </tbody>
                </table>
            `;
        } else {
            tableHtml += "<h3>Turna Uçuşları</h3><p>Hiç uçuş bulunamadı.</p>";
        }
        flightResults.innerHTML = tableHtml;
    } catch (error) {
        console.error("Hata:", error);
        flightResults.innerHTML = "<p>Bir hata oluştu. Lütfen tekrar deneyin.</p>";
    } finally {
        loader.style.display = "none";
    }
});

function buyTicket(flightId) {
    alert("Satın alınacak uçuş ID: " + flightId);
    // Buraya satın alma işlemini tetikleyecek kod ekleyin.
}