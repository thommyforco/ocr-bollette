from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
CORS(app)

# Chiave pubblica gratuita di test fornita da OCR.space
OCR_API_KEY = "helloworld"


def estrai_dati_da_testo(testo_completo):
  # Ripristina qui le tue regex per trovare POD, PDR e Prezzo Unitario
  # Esempio POD (IT...)
  pod_match = re.search(r'IT[0-9]{3}E[0-9]{8}', testo_completo, re.IGNORECASE)
  codice_pod = pod_match.group(0) if pod_match else None

  # Esempio PDR (14 cifre)
  pdr_match = re.search(r'\b[0-9]{14}\b', testo_completo)
  codice_pdr = pdr_match.group(0) if pdr_match else None

  # Esempio Prezzo Unitario
  prezzo_match = re.search(r'([0-9]+[.,][0-9]+)\s*(€/kWh|€/Smc|€|euro)?\s*(kwh|smc)', testo_completo, re.IGNORECASE)
  prezzo_unitario = prezzo_match.group(1) if prezzo_match else None

  return {
    "codice_pod_luce": codice_pod,
    "codice_pdr_gas": codice_pdr,
    "prezzo_unitario": prezzo_unitario
  }


@app.route('/api/estrai-testo', methods=['POST'])
def estrai_testo():
  if 'file' not in request.files:
    return jsonify({"errore": "Nessun file ricevuto"}), 400

  file = request.files['file']

  try:
    # Invia l'immagine direttamente all'API gratuita di OCR.space
    payload = {
      'apikey': OCR_API_KEY,
      'language': 'ita',
      'isOverlayRequired': False
    }
    files = {'file': (file.filename, file.read(), file.content_type)}

    response = requests.post('https://api.ocr.space/parse/image', data=payload, files=files)
    result = response.json()

    if result.get('IsErroredOnProcessing'):
      return jsonify({"errore": "Errore durante l'elaborazione OCR esterna"}), 500

    # Estrae tutto il testo riconosciuto dall'API
    parsed_results = result.get('ParsedResults', [])
    testo_completo = ""
    if parsed_results:
      testo_completo = parsed_results[0].get('ParsedText', '')

    # Elabora il testo con le tue regex
    dati_estratto = estrai_dati_da_testo(testo_completo)

    return jsonify(dati_estratto)

  except Exception as e:
    return jsonify({"errore": str(e)}), 500


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)
