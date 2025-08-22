# Calendario de Clases de Idiomas

Esta aplicación permite generar, visualizar y gestionar un calendario de clases de idiomas, con soporte de exportación a Excel y sincronización con SharePoint.  

---

## 1. Estructura general de la UI

La ventana principal (`MainWindow`) organiza todos los paneles:

### **Header**
- Indicadores de estado:
  - Base de datos (BD)
  - SharePoint (SP)
- Última sincronización

### **ConfigPanel** (scrollable)
- **ConexionesPanel** → botones de test BD y SharePoint.
- **FechasPanel** → selección de rango de fechas.
- **HolidayPanel** → gestión de festivos (añadir, eliminar, presets).
- **LogPanel** → visor de logs en tiempo real.

### **MainPanel**
- Vista previa del calendario en un grid con filtros de fecha.
- Botones de acción:
  - Generar calendario
  - Exportar calendario
  - Cargar calendario
  - Subir a SharePoint

### **StatusBar**
- Barra de progreso y texto de estado.
- Botón "Show Logs" que muestra el LogPanel.

---

## 2. Flujo de generación de calendario

1. El usuario selecciona fechas en **FechasPanel**.
2. Hace clic en **"Generar calendario"** (`MainPanel.generate_btn`).
3. Se llama a `App.generate_calendar()` → delega en `CalendarManager.generate_calendar()`.
4. Dentro de `CalendarManager.generate_calendar()`:
   - Verifica conexión a la BD (`self.app.db_manager.test_connection()`).
   - Obtiene fechas desde `FechasPanel.get_dates()`.
   - Convierte fechas a `datetime`.
   - Muestra feedback en `StatusBar`: `"Generando calendario..."`.
   - Llama a `CalendarService.generate_calendar(start_date, end_date, sql_query, festivos)`.
5. Dentro de `CalendarService.generate_calendar()`:
   - Valida que `start_date <= end_date`.
   - Llama a `db_service.read_clases(sql_query)` para obtener datos de clases.
   - Si hay resultados, llama a `generate_calendar_from_df()`:
     - Recorre cada clase y calcula fechas de sesiones según el campo `Dia`.
     - Filtra días que coinciden con festivos.
     - Genera un `DataFrame` con columnas:  
       `"Título","PERNR","Nombre","Mail","Fecha","Grupo","Idioma","Estado","Aviso24h","Comentarios"`.
6. `CalendarManager` guarda el `DataFrame` en `self.app.calendar_df`.
7. Llama a `_complete_calendar_generation()`:
   - Actualiza vista previa (`MainPanel.refresh_data_grid()`).
   - Actualiza `StatusBar` y registra evento en log.

---

## 3. Exportación del calendario

- Botón **"Exportar calendario"** (`MainPanel.export_btn`) → `App.export_cal()` → `CalendarManager.export_cal()`.
- Si `calendar_df` no está vacío:
  - Llama a `ExcelService.exportar_calendario(df)`.
  - Abre diálogo de selección de fichero (`tkinter.filedialog`).
  - Guarda Excel y actualiza `StatusBar` y log.

---

## 4. Carga desde Excel

- Botón **"Cargar calendario"** (`MainPanel.preview_btn`) → `App.load_cal()` → `CalendarManager.load_cal()`.
- Llama a `ExcelService.cargar_calendario()`.
- Abre diálogo de selección de fichero.
- Lee Excel en `DataFrame`.
- Actualiza `self.app.calendar_df`.
- Refresca vista previa (`MainPanel.refresh_data_grid()`) y log.

---

## 5. Gestión de festivos

- **HolidayPanel**:
  - Añadir fecha manual → parsea a `YYYY-MM-DD` → guarda en `self.app.holidays`.
  - Añadir preset ES → añade festivos nacionales del año actual.
  - Eliminar o limpiar → actualiza lista y log.
- Persistencia:
  - `HolidayService.save_festivos(festivos)` guarda en JSON (`festivos.json`).
  - `HolidayService.load_festivos()` carga al iniciar la app.

---

## 6. Conexión y sincronización

- **ConexionesPanel**:
  - Test BD → `App.test_database_connection()`.
  - Test SharePoint → `App.authenticate_sharepoint()`.
- **Botón "Subir a SharePoint"** → `App.sync_to_sharepoint()`.
- La lógica de sincronización gestiona la subida del calendario generado al sitio SharePoint.

---

## 7. Logs y status

- **LogPanel** → `LogManager` escribe logs en `CTkTextbox` en tiempo real.
- **StatusBar** → actualiza mensajes de progreso, porcentaje y estados de conexión.

---

## 8. Notas adicionales

- La aplicación usa **CustomTkinter** y **tkcalendar** para una UI moderna y scrollable.
- Todos los paneles están conectados con la clase `App`, que centraliza estados como `calendar_df`, `holidays` y `class_data`.
- Logs y status permiten un seguimiento completo de la actividad de la app.
- La exportación y carga de Excel permiten compatibilidad con otras herramientas.

---

## 9. Resumen gráfico de flujo

```mermaid
flowchart TD
    A[Usuario] -->|Selecciona fechas| B[FechasPanel]
    B -->|Genera calendario| C[MainPanel.generate_btn]
    C --> D[CalendarManager.generate_calendar]
    D --> E[CalendarService.generate_calendar]
    E --> F[db_service.read_clases]
    F --> G[DataFrame → DataFrame final]
    D --> H[_complete_calendar_generation]
    H --> I[MainPanel.refresh_data_grid]
    H --> J[StatusBar update]
    H --> K[Log update]
    A -->|Exporta calendario| L[MainPanel.export_btn]
    L --> M[ExcelService.exportar_calendario]
    A -->|Carga calendario| N[MainPanel.preview_btn]
    N --> O[ExcelService.cargar_calendario]
    A -->|Gestiona festivos| P[HolidayPanel → HolidayService.save/load]

---

## Flujo de la aplicación: Calendario de Clases de Idiomas

```mermaid
flowchart TD
    A[main.py] --> B[MainWindow]
    B --> C[Header]
    B --> D[ConfigPanel]
    B --> E[MainPanel]
    B --> F[StatusBar]

    %% ConfigPanel components
    D --> D1[ConexionesPanel]
    D --> D2[FechasPanel]
    D --> D3[HolidayPanel]
    D --> D4[LogPanel]

    %% MainPanel actions
    E -->|Generar calendario| G[CalendarManager.generate_calendar]
    E -->|Exportar calendario| H[CalendarManager.export_cal]
    E -->|Cargar calendario| I[CalendarManager.load_cal]
    E -->|Subir a SharePoint| J[SharePointManager.sync_to_sharepoint]

    %% CalendarManager interacts with services
    G --> K[CalendarService.generate_calendar]
    K --> L[DBService.read_clases]
    K --> M[HolidayService.load_festivos]
    
    H --> N[ExcelService.exportar_calendario]
    I --> O[ExcelService.cargar_calendario]

    J --> P[SharePointService.upload_calendar]

    %% HolidayPanel actions
    D3 -->|Añadir/Borrar festivo| M
    D3 -->|Guardar festivos| M[HolidayService.save_festivos]

    %% Log flow
    D4 --> Q[LogManager]
    G --> Q
    H --> Q
    I --> Q
    J --> Q

    %% StatusBar updates
    G --> F
    H --> F
    I --> F
    J --> F

