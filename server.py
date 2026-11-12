import asyncio
import json
import os
import http
import websockets

utenti_connessi = {}

async def health_check(connection, request):
    if request.path == "/healthz" or request.headers.get("Upgrade", "").lower() != "websocket":
        return connection.respond(http.HTTPStatus.OK, "CraGiChat Server Online\n")
    return None

async def gestisci_connessione(websocket):
    numero_utente = None
    try:
        async for messaggio in websocket:
            dati = json.loads(messaggio)

            # Registrazione numero utente
            if "registra" in dati:
                numero_utente = dati["registra"]
                utenti_connessi[numero_utente] = websocket
                print(f"[+] Utente connesso: {numero_utente}")
                continue

            # Inoltro messaggio, vocale, foto, file o stato "sta scrivendo..."
            destinatario = dati.get("a")
            tipo = dati.get("tipo", "testo")
            testo = dati.get("testo", "")

            if destinatario in utenti_connessi:
                risposta = json.dumps({
                    "mittente": numero_utente,
                    "tipo": tipo,
                    "testo": testo
                })
                await utenti_connessi[destinatario].send(risposta)
            else:
                if tipo != "typing":
                    avviso = json.dumps({
                        "mittente": "Server",
                        "tipo": "testo",
                        "testo": f"{destinatario} non è online al momento."
                    })
                    await websocket.send(avviso)

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if numero_utente and utenti_connessi.get(numero_utente) == websocket:
            del utenti_connessi[numero_utente]
            print(f"[-] Utente disconnesso: {numero_utente}")

async def main():
    port = int(os.environ.get("PORT", 8765))
    print(f"Avvio server CraGiChat sulla porta {port}...")
    async with websockets.serve(gestisci_connessione, "0.0.0.0", port, process_request=health_check):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())