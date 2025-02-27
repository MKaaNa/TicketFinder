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
        let enuygunFlights = data.filter(flight => flight.kaynak === "Enuygun")
            .map(flight => `<li>ID: ${flight.flight_id || "Bilinmiyor"} - ${flight.ozet}</li>`).join("");
        let obiletFlights = data.filter(flight => flight.kaynak === "Obilet")
            .map(flight => `<li>ID: ${flight.flight_id || "Bilinmiyor"} - ${flight.havayolu} - ${flight.fiyat} - ${flight.kalkış_saati}</li>`).join("");
        let turnaFlights = data.filter(flight => flight.kaynak === "Turna")
            .map(flight => `<li>${flight.ozet}</li>`).join("");
        flightResults.innerHTML = `
            <h3>Enuygun Uçuşları</h3>
            <ul>${enuygunFlights || "<p>Hiç uçuş bulunamadı.</p>"}</ul>
            <h3>Obilet Uçuşları</h3>
            <ul>${obiletFlights || "<p>Hiç uçuş bulunamadı.</p>"}</ul>
            <h3>Turna Uçuşları</h3>
            <ul>${turnaFlights || "<p>Hiç uçuş bulunamadı.</p>"}</ul>
        `;
    } catch (error) {
        console.error("Hata:", error);
        flightResults.innerHTML = "<p>Bir hata oluştu. Lütfen tekrar deneyin.</p>";
    } finally {
        loader.style.display = "none";
    }
});