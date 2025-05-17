document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("complaintForm");
    const addressChoice = document.getElementById("addressChoice");
    const manualSection = document.getElementById("manualAddressSection");
    const autoSection = document.getElementById("autoLocationSection");
    const getLocationBtn = document.getElementById("getLocationBtn");
    const locationStatus = document.getElementById("locationStatus");
    const complaintImage = document.getElementById("complaintImage");
    const imagePreview = document.getElementById("imagePreview");
    const autoAddress = document.getElementById("autoAddress");

    addressChoice.addEventListener("change", function() {
        const isManual = this.value === "manual";
        manualSection.style.display = isManual ? "block" : "none";
        autoSection.style.display = isManual ? "none" : "block";
    });

    complaintImage.addEventListener("change", function(e) {
        const file = e.target.files[0];
        if (file && file.type.startsWith("image/")) {
            const reader = new FileReader();
            reader.onload = function(event) {
                imagePreview.src = event.target.result;
                imagePreview.style.display = "block";
            };
            reader.readAsDataURL(file);
        } else if (file) {
            alert("Please select a valid image file (JPEG, PNG)");
            this.value = "";
        }
    });

    getLocationBtn.addEventListener("click", async function() {
        locationStatus.textContent = "Detecting your exact location...";
        locationStatus.style.color = "#2e7d32";
        getLocationBtn.disabled = true;
        getLocationBtn.textContent = "🛰️ Locating...";

        try {
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                });
            });

            const { latitude, longitude } = position.coords;
            const address = await getExactAddress(latitude, longitude);

            // 3. Update form fields
            autoAddress.value = address;
            document.getElementById("latitude").value = latitude;
            document.getElementById("longitude").value = longitude;
            document.getElementById("exactAddress").value = address;

            locationStatus.textContent = "Exact address found!";
            locationStatus.style.color = "#2e7d32";
            
        } catch (error) {
            let message = "Error getting location";
            if (error.code === 1) message = "Permission denied - please allow location access";
            if (error.code === 2) message = "Position unavailable (try outdoors)";
            if (error.code === 3) message = "Timeout - try again";
            
            locationStatus.textContent = message;
            locationStatus.style.color = "#e53935";
        } finally {
            getLocationBtn.disabled = false;
            getLocationBtn.textContent = "📍 Get Exact Location";
        }
    });

    async function getExactAddress(lat, lon) {
        try {
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            const response = await fetch(
                `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`
            );
            const data = await response.json();
            
            if (data.address) {
                const addr = data.address;
                return [
                    addr.house_number && addr.road ? `${addr.house_number} ${addr.road}` : addr.road,
                    addr.neighbourhood || addr.suburb,
                    addr.city || addr.town || addr.village,
                    addr.postcode,
                    addr.country
                ].filter(Boolean).join(", ");
            }
            return data.display_name || `Near ${lat.toFixed(5)}, ${lon.toFixed(5)}`;
        } catch (error) {
            console.error("Geocoding error:", error);
            return `Near ${lat.toFixed(5)}, ${lon.toFixed(5)}`;
        }
    }

    form.addEventListener("submit", function(e) {
        e.preventDefault();
        
        if (!complaintImage.files.length) {
            alert("Please upload an image");
            return;
        }
        
        const locationData = {
            method: addressChoice.value,
            address: addressChoice.value === "manual" 
                ? document.getElementById("address").value 
                : autoAddress.value,
            exactAddress: document.getElementById("exactAddress").value,
            coordinates: addressChoice.value === "auto"
                ? `${document.getElementById("latitude").value},${document.getElementById("longitude").value}`
                : null
        };
        
        console.log("Submitting:", {
            image: complaintImage.files[0].name,
            ...locationData,
            description: document.getElementById("description").value || "None"
        });
        
        alert(`Report submitted successfully!\n\nAddress: ${locationData.address}`);
        form.reset();
        imagePreview.style.display = "none";
    });
});
