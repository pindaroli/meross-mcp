# meross-mcp

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Protocol](https://img.shields.io/badge/MCP-Model_Context_Protocol-purple.svg)](https://modelcontextprotocol.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)

Zero-install **Model Context Protocol (MCP)** server, **REST API Gateway** and Python library for **Meross** smart plugs (MSS110, MSS210, MSS310, MSS305, MSS425E power strips and compatible devices), powered by [`meross-iot`](https://pypi.org/project/meross-iot/).

---

## 🌟 Caratteristiche Chiave

* **Dual Gateway (MCP + REST)**: Un unico server leggero asincrono che serve contemporaneamente:
  * L'endpoint **MCP** (`/mcp` o `stdio`) per agenti AI (**Google Antigravity**, **Claude Desktop**, **Cursor**).
  * Le **REST API** (`/api/v1/devices/...`) per dashboard (**Homepage**), script bash, allarmi **UPS NUT** e webhook **n8n**.
  * Documentazione interattiva automatica **Swagger UI** su `/docs`.
* **Zero-Install On-Demand**: Eseguibile al volo senza dover clonare il repository o configurare virtualenv persistenti, grazie a `uvx`.
* **Connection Pooling Persistente**: Mantiene in memoria una singola connessione asincrona MQTT over TLS verso i broker Meross, eliminando latenze di login e prevenendo rate-limiting dal cloud.
* **Telemetria Energetica**: Lettura in tempo reale dei consumi di corrente (Watt, Volt, Ampere) per modelli con misuratore (MSS310, MSS305).
* **Controllo Canali**: Supporto sia per prese singole sia per ciabatte multipresa a canali indipendenti (MSS425E).
* **Libreria Python Riusabile**: Importabile direttamente all'interno di progetti Python personalizzati (`from meross_mcp import MerossClientManager`).

---

## 🚀 Guida Rapida: Esecuzione Zero-Install

Non è richiesta alcuna installazione permanente. Se hai [`uv`](https://github.com/astral-sh/uv) installato:

### 1. Avvio del Dual Gateway (REST + MCP + Swagger UI)
```bash
export MEROSS_EMAIL="tuo_account@meross.com"
export MEROSS_PASSWORD="tua_password_meross"

# Esecuzione diretta da GitHub:
uvx --from git+https://github.com/pindaroli/meross-mcp.git meross-mcp --port 8112
```

Una volta avviato:
* **Swagger UI (Browser)**: [http://localhost:8112/docs](http://localhost:8112/docs)
* **Probe di Salute**: [http://localhost:8112/healthz](http://localhost:8112/healthz)
* **Endpoint MCP**: `http://localhost:8112/mcp`

---

## 🤖 Configurazione Client MCP (Google Antigravity / Claude Desktop)

Aggiungi il blocco di configurazione nel tuo file `mcp_config.json`:

### Modalità Stdio Locale:
```json
{
  "mcpServers": {
    "meross": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/pindaroli/meross-mcp.git",
        "meross-mcp",
        "--transport",
        "stdio"
      ],
      "env": {
        "MEROSS_EMAIL": "tuo_account@meross.com",
        "MEROSS_PASSWORD": "tua_password_meross"
      }
    }
  }
}
```

### Strumenti MCP Disponibili:
* `meross_list_devices`: Elenco delle prese registrate con ID univoco, nome, modello, canali e stato online.
* `meross_get_device_state`: Ispezione dettagliata dello stato di relè, firmware e segnale Wi-Fi.
* `meross_turn_on`: Accensione presa (con selezione facoltativa del `channel`).
* `meross_turn_off`: Spegnimento presa (con selezione facoltativa del `channel`).
* `meross_toggle`: Inversione stato ON/OFF.
* `meross_get_electricity`: Rilevazione telemetria (potenza in Watt, tensione in Volt, corrente in Ampere).

---

## 🌐 REST API Endpoints (per Homepage, Script & Automazioni)

| Metodo | Endpoint | Parametri | Descrizione |
| :--- | :--- | :--- | :--- |
| `GET` | `/healthz` | *nessuno* | Health check per Uptime Kuma o container probe. |
| `GET` | `/docs` | *nessuno* | Interfaccia Swagger UI interattiva. |
| `GET` | `/api/v1/devices` | *nessuno* | Lista di tutte le prese con stato corrente. |
| `GET` | `/api/v1/devices/{id}` | `id` | Dettaglio di una presa (UUID o nome). |
| `POST` | `/api/v1/devices/{id}/on` | `?channel=0` | Accende la presa o un canale specifico. |
| `POST` | `/api/v1/devices/{id}/off` | `?channel=0` | Spegne la presa o un canale specifico. |
| `POST` | `/api/v1/devices/{id}/toggle` | `?channel=0` | Inverte lo stato relè della presa. |
| `GET` | `/api/v1/devices/{id}/power` | *nessuno* | Lettura telemetria istantanea ($W$, $V$, $A$). |

### Esempi Rapidi `curl`:
```bash
# Accendi la stampante 3D
curl -X POST "http://localhost:8112/api/v1/devices/stampante/on"

# Leggi i consumi istantanei del PC
curl "http://localhost:8112/api/v1/devices/pc-gaming/power"
```

---

## 📦 Utilizzo come Libreria Python

```bash
pip install meross-mcp
# oppure con uv
uv add meross-mcp
```

```python
import asyncio
from meross_mcp import MerossClientManager, MerossSettings

async def main():
    settings = MerossSettings(
        email="tuo_account@meross.com",
        password="tua_password_meross",
    )
    async with MerossClientManager(settings) as client:
        devices = await client.list_devices()
        for dev in devices:
            print(f"Presa: {dev.name} ({dev.model}) - Online: {dev.online}")

asyncio.run(main())
```

---

## 📄 Licenza

Rilasciato sotto licenza [MIT](LICENSE). Copyright (c) 2026 Olindo Pindaroli.
