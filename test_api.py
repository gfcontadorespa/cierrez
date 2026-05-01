import requests

payload = {
    "company_id": 1,
    "branch_id": 1,
    "z_number": "Z-TEST",
    "date_closed": "2026-05-01",
    "taxable_sales": 12.0,
    "exempt_sales": 0.0,
    "tax_amount": 0.84,
    "total_sales": 12.0,
    "total_receipt": 12.84,
    "difference_amount": 0.0,
    "image_url": "test_url",
    "pos_receipt_url": "test_url",
    "deposit_receipt_url": None,
    "payments": [
        {"payment_method_id": 1, "amount": 10.0},
        {"payment_method_id": 2, "amount": 2.84}
    ]
}

try:
    res = requests.post("http://localhost:8000/api/cierres", json=payload)
    print("Status:", res.status_code)
    print("Response:", res.text)
except Exception as e:
    print("Exception:", e)

