document.addEventListener('DOMContentLoaded', function() {
    const isLoggedIn = document.body.getAttribute('data-is-logged-in') === 'True';

    document.getElementById('pesananAndaLink').addEventListener('click', handlePesananAndaClick);

    function toggleDetailPesanan() {
        var detailPesanan = document.getElementById('detailPesanan');
        if (detailPesanan.style.display === 'none' || detailPesanan.style.display === '') {
            detailPesanan.style.display = 'block';
        } else {
            detailPesanan.style.display = 'none';
        }
    }

    function togglePembayaran() {
        var paymentPopup = document.getElementById('paymentPopup');
        var detailPesanan = document.getElementById('detailPesanan');
        if (paymentPopup.style.display === 'none' || paymentPopup.style.display === '') {
            paymentPopup.style.display = 'block';
            detailPesanan.style.display = 'none';
        } else {
            paymentPopup.style.display = 'none';
        }
    }

    function togglePembayaranBack() {
        var paymentPopup = document.getElementById('paymentPopup');
        var detailPesanan = document.getElementById('detailPesanan');
        paymentPopup.style.display = 'none';
        detailPesanan.style.display = 'block';
    }

    function toggleLoginPopup() {
        var loginPopup = document.getElementById('loginPopup');
        if (loginPopup.style.display === 'none' || loginPopup.style.display === '') {
            loginPopup.style.display = 'block';
        } else {
            loginPopup.style.display = 'none';
        }
    }

    function tampilkanDetailPesanan() {
        var detailPesananItems = document.getElementById('detailPesananItems');
        var totalHarga = 0;
        var menuItems = document.querySelectorAll('.menu-item');
        detailPesananItems.innerHTML = '';
        menuItems.forEach(function(item) {
            var quantity = parseInt(item.querySelector('input[type="text"]').value);
            if (quantity > 0) {
                var itemName = item.querySelector('h3').innerText;
                var itemPrice = parseInt(item.querySelector('.price').innerText.replace('Rp. ', '').replace('.', ''));
                var totalPrice = quantity * itemPrice;
                detailPesananItems.innerHTML += '<p>' + itemName + ' x ' + quantity + ' = Rp. ' + totalPrice.toLocaleString() + '</p>';
                totalHarga += totalPrice;
            }
        });
        document.getElementById('totalHarga').innerText = 'Rp. ' + totalHarga.toLocaleString();
    }

    document.querySelectorAll('.menu-item').forEach(item => {
        const quantityInput = item.querySelector('input[type="text"]');
        const plusButton = item.querySelector('.plus');
        const minusButton = item.querySelector('.minus');

        plusButton.addEventListener('click', () => {
            quantityInput.value = parseInt(quantityInput.value) + 1;
            checkPesanan();
            tampilkanDetailPesanan();
        });

        minusButton.addEventListener('click', () => {
            if (parseInt(quantityInput.value) > 0) {
                quantityInput.value = parseInt(quantityInput.value) - 1;
                checkPesanan();
                tampilkanDetailPesanan();
            }
        });
    });

    function checkPesanan() {
        const pesananAndaButton = document.getElementById('pesananAnda');
        const totalPesanan = Array.from(document.querySelectorAll('input[type="text"]')).reduce((total, input) => total + parseInt(input.value), 0);
        if (totalPesanan > 0) {
            pesananAndaButton.style.display = 'block';
        } else {
            pesananAndaButton.style.display = 'none';
        }
    }

    function handlePesananAndaClick() {
        if (isLoggedIn) {
            toggleDetailPesanan();
            tampilkanDetailPesanan();
        } else {
            toggleLoginPopup();
        }
    }

    function showQris() {
        document.getElementById('qrisDetails').style.display = 'block';
        hideBankDetails();
    }

    function hideQris() {
        document.getElementById('qrisDetails').style.display = 'none';
        hideBankDetails();
    }

    function hideBankDetails() {
        document.querySelectorAll('.bank-details, .bank-transfer-details').forEach(div => {
            div.style.display = 'none';
        });
    }

    function pesanSekarang() {
        const items = [];
        document.querySelectorAll('.menu-item').forEach(item => {
            const quantity = parseInt(item.querySelector('input[type="text"]').value);
            if (quantity > 0) {
                const itemName = item.querySelector('h3').innerText;
                const itemPrice = parseInt(item.querySelector('.price').innerText.replace('Rp. ', '').replace('.', ''));
                items.push({
                    name: itemName,
                    price: itemPrice,
                    quantity: quantity
                });
            }
        });
        const totalHarga = document.getElementById('totalHarga').innerText.replace('Rp. ', '').replace(',', '');

        const orderData = {
            items: items,
            total: parseInt(totalHarga),
            payment_method: document.querySelector('input[name="metode_pembayaran"]:checked').value
        };

        fetch('/pesan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.location.href = `/pesanan_anda/${data.pesanan_id}`;
            } else {
                alert('Terjadi kesalahan: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Terjadi kesalahan. Silakan coba lagi.');
        });
    }

    function batalkanPesanan() {
        toggleDetailPesanan();
        resetPesanan();
        tampilkanDetailPesanan();
    }

    function resetPesanan() {
        document.querySelectorAll('.menu-item input[type="text"]').forEach(input => {
            input.value = 0;
        });
        checkPesanan();
    }

    document.querySelectorAll('input[name="metode_pembayaran"]').forEach(radio => {
        radio.addEventListener('change', () => {
            hideQris();
            if (radio.value === 'rekening_bank') {
                document.querySelector('.bank-details').style.display = 'block';
            } else if (radio.value === 'transfer_antar_bank') {
                document.querySelector('.bank-transfer-details').style.display = 'block';
            } else if (radio.value === 'qris') {
                showQris();
            }
        });
    });
});
