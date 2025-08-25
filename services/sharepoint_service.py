# File: services/sharepoint_service.py
from datetime import date, datetime
import math
import os

import requests
import msal
import webbrowser
import json

from config import (
    SP_CLIENT_ID, 
    SP_TENANT_ID, 
    USER_EMAIL, 
    SP_SITE_HOST, 
    SP_SITE_PATH, 
    SP_LIST_NAME
)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPES = ["Sites.ReadWrite.All"]
TOKEN_CACHE_FILE = "token_cache.bin"

class SharePointService:
    def __init__(self, log_callback=None):
        self.log_fn = log_callback or (lambda x: None)
        self._graph = None
        self._site_id = None
        self._list_id = None
        self.client = None
        self._column_map = None
        
    @property
    def is_authenticated(self):
        return self.client is not None and self.client.token is not None
        
    def initialize(self):
        """Initialize Graph client"""
        if self.client is None:
            self.client = GraphDelegatedClient(
                SP_CLIENT_ID,
                SP_TENANT_ID,
                USER_EMAIL,
                self.log_fn
            )
        return self.client
        
    def authenticate(self):
        """Authenticate and resolve site/list"""
        try:
            self.initialize()
            return self.resolve_site_and_list()
        except Exception as e:
            self.log_fn(f"Error en autenticación: {str(e)}")
            return False
            
    def resolve_site_and_list(self):
        """Resolve SharePoint site and list IDs"""
        site_graph_id = f"{SP_SITE_HOST}:{SP_SITE_PATH}"
        self.log_fn(f"Resolviendo Site por ruta {site_graph_id}...")
        
        self._site_id = self.client.get_site_id_by_path(site_graph_id)
        if not self._site_id:
            self.log_fn("No se pudo resolver site_id")
            return False
            
        self._list_id = self.client.get_list_id_by_name(self._site_id, SP_LIST_NAME)
        if not self._list_id:
            self.log_fn(f"No se encontró la lista '{SP_LIST_NAME}'")
            return False
            
        self.log_fn(f"Conectado. SiteID={self._site_id} | ListID={self._list_id}")
        
        # Get item count
        item_count = self.client.get_list_item_count(self._site_id, self._list_id)
        if item_count != -1:
            self.log_fn(f"La lista '{SP_LIST_NAME}' contiene actualmente {item_count} elementos.")
            
        return True
    

    def sync_data(self, data):
        """Borra todos los elementos y luego inserta nuevos registros en SharePoint usando batch"""
        self.log_fn(f"🔎 sync_data recibe tipo: {type(data)} con len={getattr(data, '__len__', 'NA')}")
        if isinstance(data, list) and data:
            self.log_fn(f"   Primer elemento: {type(data[0])} -> {data[0]}")

        if not all([self.client, self._site_id, self._list_id]):
            raise ValueError("SharePoint not properly initialized")
        
        if data is None or len(data) == 0:
            self.log_fn("⚠️ No hay registros para insertar en SharePoint")
            return False
                
        # --- Borrado de todos los elementos ---
        self.log_fn("🔄 Iniciando borrado de elementos de la lista...")
        url = f"{GRAPH_BASE}/sites/{self._site_id}/lists/{self._list_id}/items?$select=id"
        total_deleted = 0

        while url:
            data_items, err, _, _ = self.client.graph_get(url)
            if err:
                self.log_fn(f"❌ Error obteniendo items: {err}")
                return False

            items = data_items.get("value", [])
            if not items:
                break

            # Dividimos en lotes de 20 (máximo permitido en Graph /batch)
            for i in range(0, len(items), 20):
                batch = items[i:i+20]
                requests_batch = {
                    "requests": [
                        {
                            "id": str(idx),
                            "method": "DELETE",
                            "url": f"/sites/{self._site_id}/lists/{self._list_id}/items/{item['id']}"
                        }
                        for idx, item in enumerate(batch)
                    ]
                }

                # ⚠️ NO machacar el parámetro `data`
                batch_resp, err, status, _ = self.client._make_request(
                    "POST",
                    f"{GRAPH_BASE}/$batch",
                    json=requests_batch
                )
                if err:
                    self.log_fn(f"❌ Error en batch delete: {err}")
                    return False
                else:
                    total_deleted += len(batch)
                    self.log_fn(f"✔️ Eliminados {len(batch)} elementos en lote")

            # Paginación
            url = data_items.get("@odata.nextLink")

        self.log_fn(f"✅ Borrado completado. Total eliminados: {total_deleted}")

        # --- Mapeo a internal names ---
        col_map = self.get_column_map()
        if not col_map:
            self.log_fn("❌ No hay mapa de columnas; no se puede continuar con la inserción.")
            return False

        # Guardas defensivas antes de mapear
        if not isinstance(data, list):
            self.log_fn(f"❌ Esperaba lista de dicts; recibí {type(data)} -> {repr(data)[:200]}")
            return False
        if data and not isinstance(data[0], dict):
            self.log_fn(f"❌ Cada fila debe ser dict; primer elemento es {type(data[0])} -> {repr(data[0])[:200]}")
            return False

        mapped_rows = self._map_rows_to_internal(data, col_map)

        # 🔍 Validación extra
        for i, row in enumerate(mapped_rows[:3]):
            self.log_fn(f"   [DEBUG] mapped_rows[{i}] = {type(row)} -> {row}")

        # --- Inserción batch ---
        self.log_fn("🔄 Iniciando inserción de nuevos elementos en la lista...")
        insert_dataframe_in_batches(
            self.client,
            self._site_id,
            self._list_id,
            mapped_rows,
            log=self.log_fn,
            batch_size=20
        )

        # --- Verificación: contar items ---
        new_count = self.client.get_list_item_count(self._site_id, self._list_id)
        if new_count != -1:
            self.log_fn(f"📈 La lista ahora contiene {new_count} elementos.")
            return new_count == len(mapped_rows)

        return True

    def get_column_map(self, force=False):
        """
        Obtiene y cachea el diccionario {displayName -> internalName} de la lista.
        También loguea la tabla display/internal.
        """
        if self._column_map is not None and not force:
            return self._column_map

        cols = self.client.get_list_columns(self._site_id, self._list_id)
        if cols is None:
            self.log_fn("❌ No se pudieron obtener las columnas de la lista para construir el mapa.")
            self._column_map = {}
            return self._column_map

        # Log de columnas
        self.log_fn("📋 Columnas de la lista (display → internal):")
        for c in cols:
            disp = c.get("displayName")
            name = c.get("name")
            flags = []
            if c.get("hidden"):
                flags.append("hidden")
            if c.get("readOnly"):
                flags.append("readOnly")
            flags_txt = f" [{'|'.join(flags)}]" if flags else ""
            self.log_fn(f"  - {disp} → {name}{flags_txt}")

        # Construimos el mapa display->internal
        self._column_map = {c.get("displayName"): c.get("name") for c in cols if c.get("displayName") and c.get("name")}
        return self._column_map

    def _sanitize_value(self, v):
        """Convierte NaN/NaT a None y formatea fechas a ISO."""
        try:
            # Soporta pandas si está disponible
            import pandas as pd
            if pd.isna(v):
                return None
        except Exception:
            # Fallback sin pandas
            if isinstance(v, float) and math.isnan(v):
                return None

        # Fechas
        if isinstance(v, (datetime, date)):
            # Para DateOnly en SharePoint basta 'YYYY-MM-DD'; si te piden DateTime, ISO también vale
            return v.isoformat()

        return v

    def _map_rows_to_internal(self, rows, col_map):
        """
        rows: lista de dicts con displayNames como claves (los del DataFrame)
        col_map: dict {displayName -> internalName}
        Devuelve lista de dicts con internal names, asegurando 'Title'.
        Convierte a texto campos como PERNR y Grupo, y omite campos con valores por defecto.
        """
        from collections import Counter
        missing = Counter()
        mapped_rows = []

        self.log_fn(f"🔎 _map_rows_to_internal recibe {len(rows)} filas, primer tipo: {type(rows[0])}")

        # Campos de SharePoint que no debemos enviar porque tienen valores por defecto
        EXCLUDE_FIELDS = {"Estado", "Aviso24h", "Observaciones"}

        # Campos que en SharePoint son texto aunque en el DataFrame vengan como números
        TEXT_FIELDS = {"PERNR", "Grupo"}

        for idx, r in enumerate(rows):
            new = {}
            for k, v in r.items():
                if k in EXCLUDE_FIELDS:
                    continue

                internal = col_map.get(k)
                if internal:
                    # Reemplazar LinkTitle por Title si existe
                    if internal.lower() == "linktitle":
                        internal = "Title"

                    # Convertir a str si SharePoint espera texto
                    if internal in TEXT_FIELDS and v is not None:
                        v = str(v)

                    new[internal] = self._sanitize_value(v)
                else:
                    missing[k] += 1

            # Asegurar 'Title' siempre presente
            if "Title" not in new:
                for candidate in ("Título", "Titulo", "Title", "Nombre"):
                    if candidate in r and r[candidate]:
                        new["Title"] = str(r[candidate])
                        break
                else:
                    new["Title"] = f"Item {idx+1}"

            # Solo campos writeable (están en col_map.values()) + Title obligatorio
            writeable = {k: v for k, v in new.items() if k in col_map.values() or k == "Title"}
            mapped_rows.append(writeable)

        if missing:
            missing_txt = ", ".join(f"{k}({c})" for k, c in missing.items())
            self.log_fn(f"⚠️ Campos del DataFrame no presentes en la lista (ignorados): {missing_txt}")

        # Log de un ejemplo mapeado
        if mapped_rows:
            try:
                import json
                self.log_fn(f"🧭 Ejemplo de fila mapeada a internal names: {json.dumps(mapped_rows[0], ensure_ascii=False)}")
            except Exception:
                pass
        
        import copy
        mapped_rows = [copy.deepcopy(r) for r in mapped_rows]
        

        return mapped_rows
    
    
class GraphDelegatedClient:
    """
    Cliente para interactuar con Microsoft Graph API usando flujo de autenticación delegada (device flow).
    """
    def __init__(self, client_id, tenant_id, user_email, log_fn):
        self.client_id = client_id
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.log = log_fn
        self.token = None
        
        self.cache = msal.SerializableTokenCache()
        if os.path.exists(TOKEN_CACHE_FILE):
            self.log(f"Cargando caché de token desde {TOKEN_CACHE_FILE}")
            self.cache.deserialize(open(TOKEN_CACHE_FILE, "r").read())                

        self.app = msal.PublicClientApplication(
            client_id,
            authority=self.authority,
            token_cache=self.cache
        )
        
        self.token = self._get_token_interactive()
    
    def save_cache(self):
        """Saves the token cache to a file if it has changed."""
        if self.cache.has_state_changed:
            self.log(f"Guardando caché de token en {TOKEN_CACHE_FILE}")
            with open(TOKEN_CACHE_FILE, "w") as cache_file:
                cache_file.write(self.cache.serialize())

    def _get_token_interactive(self):
        """Obtiene un token, primero desde la caché, y si no, interactivamente."""
        accounts = self.app.get_accounts()
        result = None

        if accounts:
            self.log(f"Cuenta encontrada en caché: {accounts[0]['username']}")
            result = self.app.acquire_token_silent(SCOPES, account=accounts[0])

        if not result:
            self.log("No hay token en caché o ha expirado. Iniciando autenticación interactiva...")
            flow = self.app.initiate_device_flow(scopes=SCOPES)
            if "user_code" not in flow:
                raise ValueError("Fallo al crear el flujo de dispositivo. Respuesta: {}".format(json.dumps(flow, indent=4)))

            self.log(f"Autenticación requerida: abre un navegador, ve a {flow['verification_uri']} e introduce el código: {flow['user_code']}")
            webbrowser.open(flow['verification_uri'])
            
            result = self.app.acquire_token_by_device_flow(flow)
            # Guardar la caché inmediatamente después de una autenticación exitosa
            self.save_cache()

        if "access_token" in result:
            self.log("Token de acceso obtenido con éxito.")
            return result['access_token']
        else:
            error_desc = result.get("error_description", "No hay descripción del error.")
            self.log(f"Error al obtener el token: {result.get('error')}\n{error_desc}")
            raise Exception(f"No se pudo obtener el token de acceso: {error_desc}")

    def _make_request(self, method, url, **kwargs):
        """Helper para realizar peticiones a la API Graph con el token de acceso."""
        if not self.token:
            self.log("Error: no hay token de acceso disponible.")
            return None, "Token no disponible", 500, None

        headers = kwargs.get("headers", {})
        headers['Authorization'] = f'Bearer {self.token}'
        headers['Accept'] = 'application/json'
        if 'json' in kwargs:
            headers['Content-Type'] = 'application/json'
        
        kwargs['headers'] = headers
        
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            
            # Para respuestas sin contenido (ej. DELETE 204)
            if response.status_code == 204:
                return None, None, response.status_code, response.headers

            return response.json(), None, response.status_code, response.headers
        except requests.exceptions.HTTPError as e:
            err_json = e.response.json() if e.response.content else {}
            error_message = err_json.get("error", {}).get("message", str(e))
            self.log(f"Error HTTP {e.response.status_code} en {method} {url}: {error_message}")
            return err_json, error_message, e.response.status_code, e.response.headers
        except Exception as e:
            self.log(f"Error inesperado en petición a Graph: {e}")
            return None, str(e), 500, None

    def graph_get(self, url, **kwargs):
        """Realiza una petición GET a la API Graph."""
        return self._make_request("GET", url, **kwargs)

    def graph_post(self, url, **kwargs):
        """Realiza una petición POST a la API Graph."""
        return self._make_request("POST", url, json=json, **kwargs)

    def get_site_id_by_path(self, site_graph_id: str):
        """Obtiene el ID de un sitio de SharePoint a partir de su ruta (hostname:/sites/path)."""
        url = f"{GRAPH_BASE}/sites/{site_graph_id}"
        self.log(f"Buscando site ID para: {site_graph_id}")
        data, err, _, _ = self.graph_get(url)
        if err:
            return None
        site_id = data.get("id")
        if site_id:
            self.log(f"Site ID encontrado: {site_id}")
        return site_id

    def get_list_id_by_name(self, site_id: str, list_name: str):
        """Obtiene el ID de una lista dentro de un sitio por su nombre."""
        url = f"{GRAPH_BASE}/sites/{site_id}/lists"
        params = {"$filter": f"displayName eq '{list_name}'"}
        self.log(f"Buscando list ID para '{list_name}' en site {site_id}")
        data, err, _, _ = self.graph_get(url, params=params)
        if err:
            return None
        lists = data.get("value", [])
        if not lists:
            return None
        list_id = lists[0].get("id")
        if list_id:
            self.log(f"List ID encontrado: {list_id}")
        return list_id

    def get_list_item_count(self, site_id: str, list_id: str):
        """Obtiene el número de elementos en una lista de SharePoint."""
        url = f"{GRAPH_BASE}/sites/{site_id}/lists/{list_id}/items"
        params = {"$select": "id", "$top": 5000}  # Aumentamos a 5000 items por página
        total_items = 0
        
        self.log(f"Obteniendo número de elementos de la lista {list_id}...")
        
        while url:
            data, err, _, _ = self.graph_get(url, params=params)
            if err:
                self.log(f"Error al intentar obtener el conteo de items. Respuesta: {err}")
                return -1
            
            items = data.get("value", [])
            total_items += len(items)
            url = data.get("@odata.nextLink")
            params = None
        
        self.log(f"La lista contiene {total_items} elementos.")
        return total_items
    
    def get_list_columns(self, site_id: str, list_id: str, select="name,displayName,hidden,readOnly"):
        """Devuelve la definición de columnas de la lista (internal name, displayName, etc.)."""
        url = f"{GRAPH_BASE}/sites/{site_id}/lists/{list_id}/columns"
        params = {"$select": select}
        data, err, _, _ = self.graph_get(url, params=params)
        if err:
            return None
        return data.get("value", [])
        

def insert_dataframe_in_batches(graph_client, site_id, list_id, rows, log, batch_size=20, progress_cb=None):
    """
    Inserta registros en la lista SharePoint usando batch requests.
    
    :param graph_client: GraphDelegatedClient
    :param site_id: ID del site SharePoint
    :param list_id: ID de la lista SharePoint
    :param rows: lista de dicts con los campos a insertar
    :param log: función para logs
    :param batch_size: máximo de items por batch (Graph limita a 20)
    :param progress_cb: callback opcional (inserted, total) para barra de progreso
    """
    total = len(rows)
    inserted = 0

    for i in range(0, total, batch_size):
        batch = rows[i:i + batch_size]

         # Log de ejemplo del primer payload
        if i == 0 and batch:
            try:
                log(f"Ejemplo de payload a insertar: {json.dumps(batch[0], ensure_ascii=False)}")
            except Exception as e:
                log(f"⚠️ No se pudo serializar el primer payload: {e}")

        # Construimos batch request
        requests_batch = {
            "requests": [
                {
                    "id": str(idx),
                    "method": "POST",
                    "url": f"/sites/{site_id}/lists/{list_id}/items",
                    "headers": {"Content-Type": "application/json"},
                    "body": {"fields": item}
                }
                for idx, item in enumerate(batch)
            ]
        }

        # 🚨 Log de la request completa (solo la primera vez, para no saturar)
        if i == 0:
            try:
                log(f"Ejemplo de batch request: {json.dumps(requests_batch, ensure_ascii=False)[:1000]}...")  # recortado a 1000 chars
            except Exception as e:
                log(f"⚠️ No se pudo serializar la batch request: {e}")

        # Ejecutamos batch
        data, err, status, _ = graph_client._make_request(
            "POST",
            f"{GRAPH_BASE}/$batch",
            json=requests_batch
        )

        if err:
            log(f"❌ Error en batch insert: {err}")
            # Opcional: podrías implementar retry aquí
        else:
            log(f"✔️ Insertados {len(batch)} elementos en batch")
            inserted += len(batch)

        # Actualizar barra de progreso si se pasa callback
        if progress_cb:
            progress_cb(inserted, total)

    log(f"✅ Inserción completada. Total insertados: {inserted}/{total}")