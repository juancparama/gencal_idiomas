# File: services/sharepoint_service.py
from datetime import date, datetime
import math
import os
import time
import uuid
from typing import Any, Dict, List, Optional
from collections import Counter
import pandas as pd
import copy
import requests
import msal
import webbrowser
import json
import asyncio
import aiohttp


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
    

    
    async def delete_all_items_async(
        self,
        max_concurrent: int = 1,
        max_retries: int = 10,
        base_delay: float = 5.0,
        progress_cb: callable = None
    ):
        """
        Borra todos los elementos de la lista en batches, con manejo de throttling (async)
        y reporte de progreso opcional.
        """
        headers = {
            "Authorization": f"Bearer {self.client.token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        # 1️⃣ Obtener todos los IDs
        url = f"{GRAPH_BASE}/sites/{self._site_id}/lists/{self._list_id}/items?$select=id"
        item_ids = []
        while url:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", base_delay))
                        self.log_fn(f"⏳ Throttling detectado. Esperando {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        continue
                    elif response.status != 200:
                        self.log_fn(f"❌ Error obteniendo items: {response.status}")
                        return False
                    data = await response.json()
                    items = data.get("value", [])
                    item_ids.extend([item["id"] for item in items])
                    url = data.get("@odata.nextLink")

        total = len(item_ids)
        self.log_fn(f"🔎 Total elementos a eliminar: {total}")

        if total == 0:
            self.log_fn("ℹ️ No hay elementos para borrar.")
            return True

        # 2️⃣ Preparar batches
        batches = [item_ids[i:i+20] for i in range(0, total, 20)]
        sem = asyncio.Semaphore(max_concurrent)
        deleted_count = 0

        async with aiohttp.ClientSession() as session:

            async def delete_batch(batch, batch_index):
                nonlocal deleted_count
                async with sem:
                    requests_batch = {
                        "requests": [
                            {
                                "id": str(uuid.uuid4()),
                                "method": "DELETE",
                                "url": f"/sites/{self._site_id}/lists/{self._list_id}/items/{item_id}"
                            }
                            for item_id in batch
                        ]
                    }

                    delay = base_delay
                    for attempt in range(1, max_retries + 1):
                        async with session.post(f"{GRAPH_BASE}/$batch", json=requests_batch, headers=headers) as response:
                            if response.status == 429:
                                retry_after = int(response.headers.get("Retry-After", delay))
                                self.log_fn(f"⏳ Batch {batch_index}: Throttling. Esperando {retry_after}s...")
                                await asyncio.sleep(retry_after)
                                continue
                            elif response.status == 200:
                                deleted_count += len(batch)
                                self.log_fn(f"✔️ Batch {batch_index}: Eliminados {len(batch)} elementos ({deleted_count}/{total})")
                                if progress_cb:
                                    progress_cb(deleted_count, total)
                                await asyncio.sleep(base_delay)
                                return True
                            else:
                                error_text = await response.text()
                                self.log_fn(f"⚠️ Batch {batch_index}: Error {response.status} - {error_text}. Reintento {attempt}/{max_retries} en {delay}s")
                                await asyncio.sleep(delay)
                                delay *= 2  # backoff exponencial

                    self.log_fn(f"❌ Batch {batch_index} falló tras {max_retries} intentos")
                    return False

            results = await asyncio.gather(*(delete_batch(batch, idx) for idx, batch in enumerate(batches)))
            ok = all(results)

        self.log_fn("✅ Borrado completado." if ok else f"⚠️ Borrado incompleto: {deleted_count}/{total} elementos eliminados")
        return ok

    def is_list_empty(self) -> bool:
        """Verifica si la lista de SharePoint está vacía."""
        count = self.client.get_list_item_count(self._site_id, self._list_id)
        if count == -1:
            self.log_fn("⚠️ No se pudo verificar si la lista está vacía.")
            return False
        self.log_fn(f"📦 Verificación: la lista contiene {count} elementos.")
        return count == 0    
    
    def sync_data(self, rows: List[Dict[str, Any]], mode: str = "replace") -> bool:
        """
        Sincroniza datos en SharePoint en dos modos:
        - 'replace': elimina TODOS los elementos y vuelve a insertar todo.
        - 'update' : NO elimina; inserta SOLO los nuevos (Title único).
        """
        import asyncio, time

        def run_async(coro):
            """Ejecuta una corrutina sin romper si ya hay loop activo."""
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # ya hay loop activo (ej. FastAPI, Flet, Jupyter)
                return asyncio.ensure_future(coro)
            else:
                return asyncio.run(coro)

        # ---- Logs iniciales y guardas defensivas ----
        self.log_fn(f"🔎 sync_data recibe tipo: {type(rows)} con len={len(rows) if rows is not None else 'NA'}; mode={mode}")

        if isinstance(rows, list) and rows:
            self.log_fn(f"   Primer elemento: {type(rows[0])} -> {rows[0]}")

        if not all([self.client, self._site_id, self._list_id]):
            raise ValueError("SharePoint not properly initialized")

        if not rows:
            self.log_fn("⚠️ No hay registros para insertar en SharePoint")
            return False

        # --- Mapeo a internal names ---
        col_map = self.get_column_map()
        if not col_map:
            self.log_fn("❌ No hay mapa de columnas; no se puede continuar.")
            return False

        if not isinstance(rows, list):
            self.log_fn(f"❌ Esperaba lista de dicts; recibí {type(rows)} -> {repr(rows)[:200]}")
            return False
        if rows and not isinstance(rows[0], dict):
            self.log_fn(f"❌ Cada fila debe ser dict; primer elemento {type(rows[0])} -> {repr(rows[0])[:200]}")
            return False

        mapped_rows = self._map_rows_to_internal(rows, col_map)

        # 🔍 Debug: primeras filas mapeadas
        for i, row in enumerate(mapped_rows[:3]):
            self.log_fn(f"   [DEBUG] mapped_rows[{i}] = {type(row)} -> {row}")

        # ------------------------------
        # MODO REPLACE: BORRA + INSERTA
        # ------------------------------
        if mode == "replace":
            self.log_fn("🔄 Iniciando borrado de elementos de la lista (modo REPLACE)...")

            # Callback opcional para progreso
            def delete_progress(deleted, total):
                self.log_fn(f"⏳ Progreso borrado: {deleted}/{total}")

            # Ejecutar borrado de manera segura en cualquier loop
            run_async(self.delete_all_items_async(progress_cb=delete_progress))

            self.log_fn("🔄 Iniciando inserción de nuevos elementos en la lista (CREAR LISTA)...")
            run_async(insert_dataframe_in_batches_async(
                self.client.token,
                self._site_id,
                self._list_id,
                mapped_rows,
                log=self.log_fn,
                batch_size=20
            ))

            new_count = self.client.get_list_item_count(self._site_id, self._list_id)
            if new_count != -1:
                self.log_fn(f"📈 La lista ahora contiene {new_count} elementos.")
                return new_count == len(mapped_rows)

            return True

        # ---------------------------
        # MODO UPDATE: SÓLO INSERTAR
        # ---------------------------
        elif mode == "update":
            before_count = self.client.get_list_item_count(self._site_id, self._list_id)
            self.log_fn(f"📦 Modo UPDATE: conteo actual = {before_count}")

            existing_titles = self.get_existing_titles()
            self.log_fn(f"🔎 Títulos existentes: {len(existing_titles)}")

            seen = set()
            new_rows = []
            for r in mapped_rows:
                t = (r.get("Title") or "").strip()
                if not t:
                    self.log_fn("⚠️ Fila sin Title -> se ignora en modo UPDATE")
                    continue
                if t in existing_titles:
                    continue
                if t in seen:
                    continue
                seen.add(t)
                new_rows.append(r)

            self.log_fn(f"🧮 Resumen UPDATE: entrada={len(mapped_rows)} | existentes={len(existing_titles)} | nuevos={len(new_rows)} | ignorados={len(mapped_rows)-len(new_rows)}")

            if not new_rows:
                self.log_fn("ℹ️ No hay registros nuevos para insertar (Title ya existentes).")
                return True

            self.log_fn("🔄 Iniciando inserción de NUEVOS elementos (UPDATE)...")
            run_async(insert_dataframe_in_batches_async(
                self.client.token,
                self._site_id,
                self._list_id,
                new_rows,
                log=self.log_fn,
                batch_size=20
            ))

            after_count = self.client.get_list_item_count(self._site_id, self._list_id)
            self.log_fn(f"📈 Conteo tras UPDATE: {after_count} (antes {before_count})")
            if before_count != -1 and after_count != -1:
                expected = before_count + len(new_rows)
                return after_count == expected

            return True

        else:
            self.log_fn(f"❌ mode desconocido: {mode}")
            return False

    def get_existing_titles(self) -> set:
        """
        Devuelve un set de Title (str) existentes en la lista.
        Usa $expand=fields($select=Title) para no traer toda la ficha.
        """
        titles = set()
        url = f"{GRAPH_BASE}/sites/{self._site_id}/lists/{self._list_id}/items"
        params = {"$select": "id", "$top": 5000, "$expand": "fields($select=Title)"}

        while url:
            data, err, _, _ = self.client.graph_get(url, params=params)
            if err:
                self.log_fn(f"❌ Error obteniendo títulos existentes: {err}")
                break
            for it in data.get("value", []):
                t = (it.get("fields") or {}).get("Title")
                if isinstance(t, str) and t.strip():
                    titles.add(t.strip())
            url = data.get("@odata.nextLink")
            params = None

        return titles


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
        missing = Counter()
        mapped_rows = []

        self.log_fn(f"🔎 _map_rows_to_internal recibe {len(rows)} filas, primer tipo: {type(rows[0])}")

        # Campos de SharePoint que no debemos enviar porque tienen valores por defecto
        EXCLUDE_FIELDS = {"Asistencia", "Aviso24h", "Observaciones"}

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
                self.log_fn(f"🧭 Ejemplo de fila mapeada a internal names: {json.dumps(mapped_rows[0], ensure_ascii=False)}")
            except Exception:
                pass    
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
        return self._make_request("POST", url, **kwargs)


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


    
    def get_list_item_count(self, site_id: str, list_id: str, base_delay: float = 5.0, max_retries: int = 5):
        """Obtiene el número de elementos en una lista de SharePoint con manejo de throttling."""
        url = f"{GRAPH_BASE}/sites/{site_id}/lists/{list_id}/items"
        params = {"$select": "id", "$top": 5000}
        total_items = 0

        self.log(f"Obteniendo número de elementos de la lista {list_id}...")

        retries = 0
        while url:
            data, err, status, headers = self.graph_get(url, params=params)

            if status == 429:
                retry_after = headers.get("Retry-After")
                delay = int(retry_after) if retry_after else base_delay * (retries + 1)
                self.log(f"⏳ Throttling detectado. Esperando {delay}s antes de reintentar...")
                time.sleep(delay)
                retries += 1
                if retries > max_retries:
                    self.log("❌ Se excedieron los reintentos por throttling.")
                    return -1
                continue

            if err:
                self.log(f"Error al intentar obtener el conteo de items. Respuesta: {err}")
                return -1

            items = data.get("value", [])
            total_items += len(items)
            url = data.get("@odata.nextLink")
            params = None
            time.sleep(base_delay)  # pausa entre páginas

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

            

async def insert_dataframe_in_batches_async(
    token: str,
    site_id: str,
    list_id: str,
    rows: list,
    log: callable,
    batch_size: int = 20,
    progress_cb: callable = None,
    max_concurrent: int = 2,
    max_retries: int = 5,
    base_delay: float = 2.0
) -> bool:
    """
    Inserta registros en SharePoint en batches, con manejo de throttling (async).
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    total = len(rows)
    log(f"📦 insert_dataframe_in_batches_async: {total} registros a insertar en batches de {batch_size}")
    inserted = 0
    batches = [rows[i:i+batch_size] for i in range(0, total, batch_size)]
    sem = asyncio.Semaphore(max_concurrent)

    async with aiohttp.ClientSession() as session:

        async def insert_batch(batch, batch_index):
            nonlocal inserted
            async with sem:
                requests_batch = {
                    "requests": [
                        {
                            "id": str(uuid.uuid4()),  # IDs únicos
                            "method": "POST",
                            "url": f"/sites/{site_id}/lists/{list_id}/items",
                            "headers": {"Content-Type": "application/json"},
                            "body": {"fields": item}
                        }
                        for item in batch
                    ]
                }

                delay = base_delay
                for attempt in range(1, max_retries + 1):
                    async with session.post(f"{GRAPH_BASE}/$batch", json=requests_batch, headers=headers) as response:
                        data = await response.json()
                        if response.status == 200:
                            # Validar respuestas internas
                            failures = [r for r in data.get("responses", []) if r.get("status", 500) >= 400]
                            if not failures:
                                inserted += len(batch)
                                log(f"✔️ Batch {batch_index}: Insertados {len(batch)} elementos ({inserted}/{total})")
                                if progress_cb:
                                    progress_cb(inserted, total)
                                return True
                            else:
                                log(f"⚠️ Batch {batch_index}: {len(failures)} fallos internos en batch.")
                                # tratar como error -> aplicar retry
                        else:
                            error_text = await response.text()
                            log(f"⚠️ Batch {batch_index}: Error {response.status} - {error_text}")

                        # Manejo de throttling
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            delay = int(retry_after)
                        else:
                            delay = delay * 2  # backoff exponencial

                        log(f"Reintento {attempt}/{max_retries} en {delay}s...")
                        await asyncio.sleep(delay)

                log(f"❌ Batch {batch_index} falló tras {max_retries} intentos")
                return False

        results = await asyncio.gather(*(insert_batch(batch, idx) for idx, batch in enumerate(batches)))
        ok = all(results)

    log("✅ Inserción completada." if ok else f"⚠️ Inserción incompleta: {inserted}/{total} registros insertados")
    return ok