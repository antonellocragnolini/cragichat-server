import asyncio
import websockets
import json
import os

utenti_connessi = {}

async def gestisci_connessione(websocket):
    try:
        async for messaggio in websocket:
            dati = json.loads(messaggio)
            
            # Registrazione dell'utente appena apre l'app
            if "registra" in dati:
                mio_numero = dati["registra"]
                utenti_connessi[mio_numero] = websocket
                print(f"Utente connesso: {mio_numero}")
            
            # Invio di un messaggio a un contatto
            elif "a" in dati:
                destinatario = dati["a"]
                
                # Trova chi sta inviando il messaggio
                mittente = None
                for num, ws in utenti_connessi.items():
                    if ws == websocket:
                        mittente = num
                        break
                        
                # Se il destinatario è online, inviagli il messaggio
                if destinatario in utenti_connessi:
                    messaggio_da_inviare = {
                        "mittente": mittente,
                        "tipo": dati.get("tipo", "testo"),
                        "testo": dati["testo"]
                    }
                    await utenti_connessi[destinatario].send(json.dumps(messaggio_da_inviare))
                else:
                    # Se è offline, avvisa chi ha scritto
                    avviso = {
                        "mittente": "Server",
                        "tipo": "testo",
                        "testo": "L'utente non è online. Il messaggio non è stato consegnato."
                    }
                    await websocket.send(json.dumps(avviso))
                    
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # Quando qualcuno chiude l'app, rimuovilo dalla memoria del server
        for num, ws in list(utenti_connessi.items()):
            if ws == websocket:
                del utenti_connessi[num]
                print(f"Utente disconnesso: {num}")
                break

async def main():
    # Prende la porta assegnata da Render (fondamentale per farlo funzionare)
    port = int(os.environ.get("PORT", 8765))
    print(f"Server in ascolto sulla porta {port}...")
    
    # 0.0.0.0 permette al server di ricevere le connessioni dai cellulari esterni
    async with websockets.serve(gestisci_connessione, "0.0.0.0", port):
        await asyncio.Future()  # Mantiene il server sempre acceso

if __name__ == "__main__":
    asyncio.run(main())
