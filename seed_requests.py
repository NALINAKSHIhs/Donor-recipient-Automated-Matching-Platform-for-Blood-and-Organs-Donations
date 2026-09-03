"""
Run this once to seed 5 sample urgent requests into the database.
    python seed_requests.py
"""

from database import init_db, add_request

init_db()

REQUESTS = [
    {
        "patient_name": "Ramesh Verma",
        "age": 52,
        "gender": "Male",
        "blood_type": "A+",
        "phone": "9911223301",
        "email": "ramesh.verma@email.com",
        "hospital": "AIIMS Delhi",
        "city": "Delhi",
        "state": "Delhi",
        "country": "India",
        "lat": 28.5672,
        "lon": 77.2100,
        "needed_organ": "Kidney",
        "urgency": "Critical",
        "notes": "Patient has end-stage renal disease. On dialysis for 2 years. Needs transplant urgently.",
    },
    {
        "patient_name": "Meena Pillai",
        "age": 45,
        "gender": "Female",
        "blood_type": "B+",
        "phone": "9911223302",
        "email": "meena.pillai@email.com",
        "hospital": "Apollo Hospital Chennai",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "country": "India",
        "lat": 13.0604,
        "lon": 80.2496,
        "needed_organ": "Blood",
        "urgency": "High",
        "notes": "Patient undergoing chemotherapy. Requires 4 units of B+ blood immediately.",
    },
    {
        "patient_name": "Sanjay Kulkarni",
        "age": 38,
        "gender": "Male",
        "blood_type": "O+",
        "phone": "9911223303",
        "email": "sanjay.kulkarni@email.com",
        "hospital": "Kokilaben Hospital Mumbai",
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "lat": 19.1360,
        "lon": 72.8296,
        "needed_organ": "Liver",
        "urgency": "Critical",
        "notes": "Acute liver failure due to viral hepatitis. Requires living donor liver transplant within 72 hours.",
    },
    {
        "patient_name": "Lakshmi Devi",
        "age": 60,
        "gender": "Female",
        "blood_type": "AB+",
        "phone": "9911223304",
        "email": "lakshmi.devi@email.com",
        "hospital": "Narayana Health Bengaluru",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "lat": 12.9010,
        "lon": 77.5963,
        "needed_organ": "Cornea",
        "urgency": "Medium",
        "notes": "Patient suffering from corneal blindness in both eyes. Waiting for transplant for 6 months.",
    },
    {
        "patient_name": "Farhan Sheikh",
        "age": 29,
        "gender": "Male",
        "blood_type": "O-",
        "phone": "9911223305",
        "email": "farhan.sheikh@email.com",
        "hospital": "Medanta Hospital Gurugram",
        "city": "Gurugram",
        "state": "Haryana",
        "country": "India",
        "lat": 28.4595,
        "lon": 77.0266,
        "needed_organ": "Bone Marrow",
        "urgency": "High",
        "notes": "Patient diagnosed with leukemia. Bone marrow transplant is the only curative option.",
    },
]

if __name__ == "__main__":
    print("Seeding 5 urgent requests...")
    for req in REQUESTS:
        req_id = add_request(req)
        print(f"  Added: {req['patient_name']} ({req['blood_type']}, {req['needed_organ']}, {req['urgency']}) -> ID #{req_id}")
    print("\nDone! 5 requests added successfully.")
