from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)
CORS(app)

VIES_URL = "https://ec.europa.eu/taxation_customs/vies/services/checkVatService"

@app.route("/")
def home():
    return "Flask VIES API läuft!"

@app.route("/vat-checker", methods=["POST"])
def check_vat():
    #print("🔵 POST 요청 받음")  # ← 추가
    data = request.get_json()
    #print("📦 받은 데이터:", data)  # ← 추가
    country = data.get("country")
    number = data.get("number")

    if not country or not number:
        return jsonify({"error": "Ländercode und USt-IdNr. sind erforderlich."}), 400

    soap_body = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                      xmlns:urn="urn:ec.europa.eu:taxud:vies:services:checkVat:types">
       <soapenv:Header/>
       <soapenv:Body>
          <urn:checkVat>
             <urn:countryCode>{country}</urn:countryCode>
             <urn:vatNumber>{number}</urn:vatNumber>
          </urn:checkVat>
       </soapenv:Body>
    </soapenv:Envelope>
    """

    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": ""
    }

    try:
        response = requests.post(VIES_URL, data=soap_body.strip(), headers=headers, timeout=10)

        if response.status_code != 200:
            return jsonify({"error": "VIES antwortet nicht."}), 502

        root = ET.fromstring(response.content)
        ns = {"ns2": "urn:ec.europa.eu:taxud:vies:services:checkVat:types"}

        valid_elem = root.find(".//ns2:valid", ns)
        name_elem = root.find(".//ns2:name", ns)
        address_elem = root.find(".//ns2:address", ns)

        valid = valid_elem.text == "true" if valid_elem is not None else False
        name = name_elem.text if name_elem is not None else "---"
        address = address_elem.text if address_elem is not None else "---"

        return jsonify({
            "valid": valid,
            "name": name,
            "address": address
        })

    except Exception as e:
        print("Fehler beim VIES-Aufruf:", e)
        return jsonify({"error": "Interner Fehler bei der Anfrage."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    #app.run(debug=True)