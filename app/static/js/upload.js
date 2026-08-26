/**
 * Image Upload, Live Preview, and Geolocation Ingestion
 */

document.addEventListener('DOMContentLoaded', () => {
    const dropzone = document.getElementById('uploadDropzone');
    const fileInput = document.getElementById('defect_image');
    const previewContainer = document.getElementById('imagePreviewContainer');
    const previewImage = document.getElementById('previewImage');
    const removeImageBtn = document.getElementById('removeImageBtn');
    
    const latInput = document.getElementById('latitude');
    const lngInput = document.getElementById('longitude');
    const addressInput = document.getElementById('address');
    const geoStatus = document.getElementById('geoStatus');
    const fetchGpsBtn = document.getElementById('fetchGpsBtn');

    // 1. Drag & Drop File Handling
    if (dropzone && fileInput) {
        dropzone.addEventListener('click', () => fileInput.click());

        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropzone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropzone.classList.remove('dragover');
            });
        });

        dropzone.addEventListener('drop', (e) => {
            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                fileInput.files = e.dataTransfer.files;
                handleFileSelect(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                handleFileSelect(e.target.files[0]);
            }
        });
    }

    function handleFileSelect(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please select an image file (JPG, PNG, WEBP).');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            previewContainer.classList.remove('d-none');
            dropzone.classList.add('d-none');
        };
        reader.readAsDataURL(file);
    }

    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', () => {
            fileInput.value = '';
            previewImage.src = '';
            previewContainer.classList.add('d-none');
            dropzone.classList.remove('d-none');
        });
    }

    // 2. Geolocation Auto-Fetch
    function captureLocation() {
        if (!navigator.geolocation) {
            if (geoStatus) geoStatus.innerHTML = '<span class="text-danger"><i class="fas fa-exclamation-circle"></i> Geolocation is not supported by your browser.</span>';
            return;
        }

        if (geoStatus) geoStatus.innerHTML = '<span class="text-primary"><i class="fas fa-spinner fa-spin"></i> Fetching precise GPS coordinates...</span>';

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const lat = position.coords.latitude.toFixed(6);
                const lng = position.coords.longitude.toFixed(6);

                if (latInput) latInput.value = lat;
                if (lngInput) lngInput.value = lng;

                if (geoStatus) {
                    geoStatus.innerHTML = `<span class="text-success"><i class="fas fa-check-circle"></i> GPS Locked: ${lat}, ${lng}</span>`;
                }

                // Reverse geocoding via OpenStreetMap Nominatim
                try {
                    const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`);
                    if (response.ok) {
                        const data = await response.json();
                        if (data.display_name && addressInput && !addressInput.value) {
                            addressInput.value = data.display_name;
                        }
                    }
                } catch (err) {
                    console.warn('Reverse geocoding offline or blocked; using fallback.');
                }
            },
            (error) => {
                let msg = 'Unable to retrieve your location.';
                if (error.code === error.PERMISSION_DENIED) {
                    msg = window.isSecureContext
                        ? 'Location permission denied. Allow location access in the browser and try again.'
                        : 'GPS needs HTTPS on this network address. Open the secure server URL and try again.';
                } else if (error.code === error.TIMEOUT) {
                    msg = 'GPS request timed out. Check device location services and try again.';
                } else if (error.code === error.POSITION_UNAVAILABLE) {
                    msg = 'Current position is unavailable. Check device location services and try again.';
                }
                if (geoStatus) geoStatus.innerHTML = `<span class="text-warning"><i class="fas fa-exclamation-triangle"></i> ${msg}</span>`;
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
    }

    if (fetchGpsBtn) {
        fetchGpsBtn.addEventListener('click', (e) => {
            e.preventDefault();
            captureLocation();
        });
    }

    // Trigger auto-fetch if on upload page
    if (dropzone && latInput && !latInput.value) {
        captureLocation();
    }
});
