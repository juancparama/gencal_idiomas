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
        """Sync data to SharePoint list"""
        if not all([self.client, self._site_id, self._list_id]):
            raise ValueError("SharePoint not properly initialized")
            
        # TODO: Implement actual sync using self.client
        return True
    
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
        
def insert_dataframe_in_batches(graph: GraphDelegatedClient, site_id, list_id, rows, log, progress_cb, batch_size=20):
    pass