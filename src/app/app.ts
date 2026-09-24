import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms'; // <-- Importazione necessaria per ngModel
import * as XLSX from 'xlsx';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule], // <-- Aggiunto FormsModule qui
  templateUrl: './app.html'
})
export class AppComponent {
  isLoading = false;
  showRisultati = false;
  risparmioCalcolato = false;
  isDragOver = false;

  // Variabili collegate direttamente agli input (ngModel)
  inputPod = '';
  inputPrezzoAttuale: number = 0;
  inputCostiAttuali: number = 144;
  inputIban = '';
  inputConsumo: number | null = null;
  inputPrezzoNuovo: number | null = null;
  inputCostiNuovi: number | null = null;
  
  risparmioTotale = 0;
  excelFile: File | null = null;

  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = true;
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = false;
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = false;
    if (event.dataTransfer?.files.length) {
      this.elaboraFile(event.dataTransfer.files[0]);
    }
  }

  onFileSelected(event: any) {
    if (event.target.files.length) {
      this.elaboraFile(event.target.files[0]);
    }
  }

  onExcelSelected(event: any) {
    if (event.target.files.length) {
      this.excelFile = event.target.files[0];
    }
  }

  async elaboraFile(file: File) {
    this.isLoading = true;
    this.showRisultati = false;
    this.risparmioCalcolato = false;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:5000/api/estrai-testo", {
        method: "POST",
        body: formData
      });
      const dati = await response.json();

      if (response.ok) {
        // Assegna i dati OCR direttamente alle variabili collegate all'interfaccia
        this.inputPod = dati.codice_pod_luce || dati.codice_pdr_gas || '';
        this.inputPrezzoAttuale = dati.prezzo_unitario ? parseFloat(dati.prezzo_unitario.replace(',', '.')) : 0;
        this.showRisultati = true;
      } else {
        alert("Errore dal server: " + dati.errore);
      }
    } catch (err) {
      alert("Errore di connessione al backend Python.");
    } finally {
      this.isLoading = false;
    }
  }

  calcolaRisparmio() {
    // Ora usa direttamente le variabili di classe, senza parametri!
    if (!this.inputConsumo || !this.inputPrezzoAttuale) {
      alert("Compila i campi necessari (Prezzo attuale e Consumo).");
      return;
    }

    // Assicurati che i campi opzionali non siano nulli (fallback a 0)
    const cons = this.inputConsumo || 0;
    const pNuovo = this.inputPrezzoNuovo || 0;
    const cNuovi = this.inputCostiNuovi || 0;

    const deltaMateria = (this.inputPrezzoAttuale * cons) - (pNuovo * cons);
    const deltaFissi = this.inputCostiAttuali - cNuovi;

    this.risparmioTotale = deltaMateria + deltaFissi;
    this.risparmioCalcolato = true;
  }

  aggiornaExcel() {
    if (!this.excelFile) {
      alert("Carica prima un file Excel di destinazione!");
      return;
    }

    const nuovaRiga = {
      "POD / PDR": this.inputPod,
      "IBAN": this.inputIban,
      "Consumo (kWh/Smc)": this.inputConsumo || 0,
      "Prezzo Vecchio (€)": this.inputPrezzoAttuale,
      "Costi Fissi Vecchi (€)": this.inputCostiAttuali,
      "Prezzo Nuovo (€)": this.inputPrezzoNuovo || 0,
      "Costi Fissi Nuovi (€)": this.inputCostiNuovi || 0,
      "Risparmio Annuo (€)": Number(this.risparmioTotale.toFixed(2))
    };

    const reader = new FileReader();
    reader.onload = (e: any) => {
      const data = new Uint8Array(e.target.result);
      const workbook = XLSX.read(data, { type: 'array' });
      const firstSheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[firstSheetName];
      const jsonSheet = XLSX.utils.sheet_to_json(worksheet);
      
      jsonSheet.push(nuovaRiga);
      
      const newWorksheet = XLSX.utils.json_to_sheet(jsonSheet);
      workbook.Sheets[firstSheetName] = newWorksheet;
      XLSX.writeFile(workbook, 'Preventivi_Aggiornati.xlsx');
    };
    reader.readAsArrayBuffer(this.excelFile);
  }
}