1. Estructura general de la UI

Ventana principal (App) → contenedor de todos los paneles:

Header

Indicadores de estado BD y SharePoint.

Última sincronización.

ConfigPanel (scrollable)

ConexionesPanel → botones test BD y SharePoint.

FechasPanel → selección de rango de fechas.

HolidayPanel → gestión de festivos (add, remove, presets).

LogPanel → visor de logs.

MainPanel

Vista previa del calendario (grid con filtros).

Botones: Generar, Exportar, Cargar, Subir a SharePoint.

StatusBar

Barra de progreso y texto de estado.

Botón "Show Logs" que muestra el log panel.

2. Flujo de generación de calendario

Usuario selecciona fechas en FechasPanel.

Usuario hace click en "Generar calendario" (MainPanel.generate_btn).

Esto llama a App.generate_calendar() → que delega en CalendarManager.generate_calendar().

Dentro de CalendarManager.generate_calendar():

Verifica conexión a la BD: self.app.db_manager.test_connection().

Obtiene fechas desde FechasPanel.get_dates().

Convierte fechas a datetime.

Muestra feedback en StatusBar: "Generando calendario...".

Llama a CalendarService.generate_calendar(start_date, end_date, sql_query, festivos).

Dentro de CalendarService.generate_calendar():

Valida que start_date <= end_date.

Llama a db_service.read_clases(sql_query) para obtener datos de clases.

Si hay resultados, llama a generate_calendar_from_df():

Recorre cada clase, calcula las fechas de las sesiones según Dia.

Filtra días que coincidan con festivos (festivos list).

Genera DataFrame con columnas: "Título","PERNR","Nombre","Mail","Fecha","Grupo","Idioma","Estado","Aviso24h","Comentarios".

CalendarManager guarda DataFrame en self.app.calendar_df.

Llama a _complete_calendar_generation():

Actualiza vista previa (MainPanel.refresh_data_grid()).

Actualiza StatusBar y log de eventos.

3. Exportación del calendario

Botón "Exportar calendario" (MainPanel.export_btn) → App.export_cal() → CalendarManager.export_cal().

Si calendar_df no está vacío:

Llama a services.excel_service.exportar_calendario(df).

Abre diálogo de selección de fichero (tkinter.filedialog.asksaveasfilename).

Guarda Excel y actualiza StatusBar y log.

4. Carga desde Excel

Botón "Cargar calendario" (MainPanel.preview_btn) → App.load_cal() → CalendarManager.load_cal().

Llama a services.excel_service.cargar_calendario().

Abre diálogo de selección de fichero.

Lee Excel en DataFrame.

Actualiza self.app.calendar_df.

Refresca vista previa (MainPanel.refresh_data_grid()) y log.

5. Gestión de festivos

HolidayPanel:

Añadir fecha manual → parsea a YYYY-MM-DD → guarda en self.app.holidays.

Añadir preset ES → añade festivos nacionales del año actual.

Remove / Clear → actualiza lista y log.

Persistencia:

services.holiday_service.save_festivos(festivos) guarda JSON.

load_festivos() carga al iniciar la app.

6. Conexión y sincronización

ConexionesPanel:

Test BD → llama App.test_database_connection().

Test SharePoint → llama App.authenticate_sharepoint().

Botón "Subir a SharePoint" → App.sync_to_sharepoint().

Lógica de sincronización (no mostrada en los ficheros que pasaste).

7. Logs y status

LogPanel → app.log_manager escribe logs en CTkTextbox.

StatusBar → actualiza mensajes de progreso, porcentaje, estados de conexión.

8. Resumen gráfico de flujo
Usuario
 ├─ Selecciona fechas → FechasPanel
 ├─ Genera calendario → MainPanel.generate_btn
 │   └─ CalendarManager.generate_calendar
 │       └─ CalendarService.generate_calendar
 │           └─ db_service.read_clases → DataFrame → DataFrame final
 │       └─ _complete_calendar_generation → MainPanel.refresh_data_grid + StatusBar + Log
 ├─ Exporta calendario → MainPanel.export_btn → ExcelService.exportar_calendario
 ├─ Carga calendario → MainPanel.preview_btn → ExcelService.cargar_calendario
 └─ Gestiona festivos → HolidayPanel → HolidayService.save/load

 # Flujo de la aplicación: Calendario de Clases de Idiomas

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