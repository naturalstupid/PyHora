"""Single-record smoke test for the batch wrapper.

Demonstrates pyjhora_batch.generate_pdf: one record in, one PDF out, headless.
Unlike driving ChartTabbed's constructor directly, the birth details below are
actually honored (the constructor kwargs are not — see wrapper.py).
"""

from pyjhora_batch import generate_pdf

RECORD = {
    "name": "Test Person",
    "date_of_birth": "1985,6,15",   # yyyy,m,d
    "time_of_birth": "10:30:00",    # hh:mm:ss (24h)
    "place_name": "Ujjain",
    "latitude": 23.5,
    "longitude": 75.75,
    "timezone": 5.5,                # hours from UTC
    "gender": "male",
}


def main():
    out = generate_pdf(RECORD, "reports/test.pdf")
    print(f"Done. Wrote {out}")


if __name__ == "__main__":
    main()
