
document.addEventListener("DOMContentLoaded", function () {

    // 1. Product search
    const searchInput = document.getElementById("searchInput");
    const productTable = document.getElementById("productTable");

    if (searchInput && productTable) {
        searchInput.addEventListener("input", function () {
            const searchText = searchInput.value.toLowerCase();
            const rows = productTable.querySelectorAll("tbody tr");

            rows.forEach(function (row) {
                const productDetails = row.innerText.toLowerCase();
                row.style.display = productDetails.includes(searchText)
                    ? ""
                    : "none";
            });
        });
    }

    // 2. Confirm before deleting a product
    const deleteForms = document.querySelectorAll(".delete-form");

    deleteForms.forEach(function (form) {
        form.addEventListener("submit", function (event) {
            const confirmed = confirm(
                "Are you sure you want to delete this product?"
            );

            if (!confirmed) {
                event.preventDefault();
            }
        });
    });

    // 3. Calculate billing item subtotal
    const priceInput = document.getElementById("price");
    const quantityInput = document.getElementById("quantity");
    const subtotalOutput = document.getElementById("subtotal");

    function calculateSubtotal() {
        if (!priceInput || !quantityInput || !subtotalOutput) {
            return;
        }

        const price = Number(priceInput.value) || 0;
        const quantity = Number(quantityInput.value) || 0;

        if (price < 0 || quantity < 0) {
            subtotalOutput.textContent = "₹0.00";
            return;
        }

        const subtotal = price * quantity;
        subtotalOutput.textContent = "₹" + subtotal.toFixed(2);
    }

    if (priceInput && quantityInput && subtotalOutput) {
        priceInput.addEventListener("input", calculateSubtotal);
        quantityInput.addEventListener("input", calculateSubtotal);
    }

    // 4. Validate product quantity
    
    // 4. Validate product form
    const productForm = document.getElementById("productForm");

    if (productForm) {
        productForm.addEventListener("submit", function (event) {
            const quantityField = productForm.querySelector(
                '[name="quantity"]'
            );
            const priceField = productForm.querySelector(
                '[name="price"]'
            );

            if (!quantityField || !priceField) {
                return;
            }

            const quantity = Number(quantityField.value);
            const price = Number(priceField.value);

            if (
                quantityField.value.trim() === "" ||
                !Number.isInteger(quantity) ||
                quantity < 0 ||
                priceField.value.trim() === "" ||
                !Number.isFinite(price) ||
                price <= 0
            ) {
                event.preventDefault();
                alert("Enter a valid positive price and non-negative whole-number quantity.");
            }
        });
    }

});