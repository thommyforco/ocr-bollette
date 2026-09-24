from flask import Flask, request, jsonify
from flask_cors import CORS
import easyocr
import re
import os

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

app = Flask(__name__)
CORS(app)


def analizza_bolletta(testo):
    # Struttura base dei dati da estrarre
    dati = {
        "codice_pod_luce": None,
        "codice_pdr_gas": None,
        "prezzo_unitario": None,
        "indirizzo_fornitura": "Non trovato",
        "intestatario_fornitura": "Non trovato",
        "costi_fissi": "Non trovato"
    }

    # 1. Trova il POD (Solitamente inizia con IT seguito da 12 caratteri alfanumerici)
    pod_match = re.search(r'(IT\d{3}[A-Z0-9]{9,10})', testo, re.IGNORECASE)
    if pod_match:
        dati["codice_pod_luce"] = pod_match.group(1)

    # 2. Trova il PDR (Solitamente è una sequenza esatta di 14 numeri)
    pdr_match = re.search(r'\b(\d{14})\b', testo)
    if pdr_match:
        dati["codice_pdr_gas"] = pdr_match.group(1)

    # 3. Trova il prezzo unitario (Cerca numeri vicini alla parola kWh o Smc)
    prezzo_match = re.search(r'([0-9]+[.,][0-9]+)\s*(€/kWh|€/Smc|€|euro)?\s*(kwh|smc)', testo, re.IGNORECASE)
    if prezzo_match:
        dati["prezzo_unitario"] = prezzo_match.group(1)

    # Nota: Intestatario, Indirizzo e Costi Fissi sono molto difficili da estrarre
    # con precisione usando solo Regex perché variano da fornitore a fornitore.
    # Spesso richiedono un'analisi della posizione del testo (bounding boxes) o un LLM.

    return dati


@app.route('/api/estrai-testo', methods=['POST'])
def estrai_testo():
    if 'file' not in request.files:
        return jsonify({"errore": "Nessun file ricevuto"}), 400

    file = request.files['file']

    try:
        reader = easyocr.Reader(['it'], gpu=False)
        img_bytes = file.read()

        # Estrai tutto il testo grezzo
        risultato = reader.readtext(img_bytes, detail=0)
        testo_completo = ' '.join(risultato)

        # Passa il testo grezzo alla funzione di filtro
        dati_puliti = analizza_bolletta(testo_completo)

        # Restituisci solo i dati strutturati
        return jsonify(dati_puliti)

    except Exception as e:
        return jsonify({"errore": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True, use_reloader=False, threaded=False)