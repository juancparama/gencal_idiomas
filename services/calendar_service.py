# File: services/calendar_service.py
from datetime import datetime, timedelta
from typing import Optional, List
import pandas as pd

class CalendarService:
    def __init__(self, db_service, log_callback=None):
        """
        Initialize calendar service
        Args:
            db_service: Database service instance
            log_callback: Optional callback for logging
        """
        self.db_service = db_service
        self.log_fn = log_callback or (lambda x: None)

    def generate_calendar(self, 
                        start_date: datetime, 
                        end_date: datetime,
                        sql_query: str,
                        festivos: Optional[List[str]] = None) -> pd.DataFrame:
        """Generar calendario completo desde la BD"""
        try:
            # Validar fechas
            if start_date > end_date:
                raise ValueError("La fecha inicio debe ser anterior o igual a fecha fin")

            # Obtener datos de BD
            df = self.db_service.read_clases(sql_query)
            if df.empty:
                self.log_fn("La consulta no devolvió resultados")
                return pd.DataFrame()

            # Generar calendario
            return self.generate_calendar_from_df(df, start_date, end_date, festivos)

        except Exception as e:
            self.log_fn(f"Error generando calendario: {str(e)}")
            raise

    def generate_calendar_from_df(self, df_clases: pd.DataFrame,
                                start_date: datetime,
                                end_date: datetime,
                                festivos: Optional[List[str]] = None) -> pd.DataFrame:
        """Generar calendario desde DataFrame existente"""
        festivos_set = set(festivos or [])
        rows = []
        start = pd.to_datetime(start_date).normalize()
        end = pd.to_datetime(end_date).normalize()

        for _, r in df_clases.iterrows():
            dia = int(r["Dia"])
            current = start
            while current <= end:
                if current.isoweekday() == dia and current.strftime("%Y-%m-%d") not in festivos_set:
                    base_date = pd.Timestamp('1900-01-01')
                    numero_dia = (current - base_date).days + 2
                    titulo = f"{r['PERNR']}-{numero_dia}-{r['Idioma'][:3].upper()}"
                    rows.append({
                        "Title": titulo,
                        "PERNR": r["PERNR"],
                        "Nombre": r["Nombre"],
                        "Mail": r["Mail"],
                        "Fecha": current.strftime("%Y-%m-%d"),
                        "Grupo": r["Grupo"],
                        "Idioma": r["Idioma"],
                        "Estado": "Pendiente",
                        "Aviso24h": "",
                        "Observaciones": ""
                    })
                current += timedelta(days=1)
        


        # ... al final de generate_calendar_from_df, justo antes del return ...
        df_out = pd.DataFrame(
            rows,
            columns=["Title", "PERNR", "Nombre", "Mail", "Fecha",
                    "Grupo", "Idioma", "Estado", "Aviso24h", "Observaciones"]
        )

        return df_out
