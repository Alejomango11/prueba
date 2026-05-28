#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Académico de Administración de Tareas - Versión 2
==========================================================
Aplicación completa para gestionar tareas académicas con funcionalidades de:
- CRUD de tareas (Crear, Leer, Actualizar, Eliminar)
- Persistencia en JSON
- Integración con Google Calendar API
- Alertas de vencimiento
- Estadísticas de productividad
- Búsqueda y filtros

Diseñado específicamente para funcionar en Google Colab.

Archivo: sistema_academico_tareas2.py
Autor: Proyecto Académico
Versión: 2.1
Fecha: Mayo 2026
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

# Importaciones para Google Calendar (con manejo de error si no están instaladas)
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.colab import auth
    from google.auth import default
    GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    GOOGLE_CALENDAR_AVAILABLE = False
    print("⚠️  Nota: Para usar Google Calendar, instala las dependencias:")
    print("   !pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")


# =============================================================================
# COLORES PARA CONSOLA (ANSI)
# =============================================================================
class Colores:
    """Clase para manejar colores en la consola."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    @staticmethod
    def print_colored(texto: str, color: str) -> None:
        """Imprime texto con color."""
        print(f"{color}{texto}{Colores.END}")


# =============================================================================
# CLASE PRINCIPAL: TAREA
# =============================================================================
class Tarea:
    """
    Representa una tarea académica con sus atributos y métodos asociados.

    Atributos:
        _nombre: Nombre/descripción de la tarea
        _fecha_entrega: Fecha límite en formato YYYY-MM-DD
        _prioridad: Nivel de prioridad (alta, media, baja)
        _estado: Estado actual (pendiente o completada)
        _google_event_id: ID del evento en Google Calendar (opcional)
    """

    def __init__(self, nombre: str, fecha_entrega: str, prioridad: str,
                 estado: str = "pendiente", google_event_id: str = None):
        """
        Constructor de la clase Tarea.

        Args:
            nombre: Nombre/descripción de la tarea
            fecha_entrega: Fecha límite en formato YYYY-MM-DD
            prioridad: Nivel de prioridad ("alta", "media" o "baja")
            estado: Estado de la tarea ("pendiente" o "completada")
            google_event_id: ID del evento en Google Calendar (opcional)
        """
        self._nombre = nombre
        self._fecha_entrega = fecha_entrega
        self._prioridad = prioridad.lower()
        self._estado = estado.lower()
        self._google_event_id = google_event_id

    # -------------------------------------------------------------------------
    # GETTERS (Métodos de acceso)
    # -------------------------------------------------------------------------
    def get_nombre(self) -> str:
        """Retorna el nombre de la tarea."""
        return self._nombre

    def get_fecha_entrega(self) -> str:
        """Retorna la fecha de entrega de la tarea."""
        return self._fecha_entrega

    def get_prioridad(self) -> str:
        """Retorna la prioridad de la tarea."""
        return self._prioridad

    def get_estado(self) -> str:
        """Retorna el estado de la tarea."""
        return self._estado

    def get_google_event_id(self) -> Optional[str]:
        """Retorna el ID del evento en Google Calendar."""
        return self._google_event_id

    # -------------------------------------------------------------------------
    # SETTERS (Métodos de modificación)
    # -------------------------------------------------------------------------
    def set_nombre(self, nombre: str) -> None:
        """Modifica el nombre de la tarea."""
        self._nombre = nombre

    def set_fecha_entrega(self, fecha_entrega: str) -> None:
        """Modifica la fecha de entrega de la tarea."""
        self._fecha_entrega = fecha_entrega

    def set_prioridad(self, prioridad: str) -> None:
        """Modifica la prioridad de la tarea."""
        self._prioridad = prioridad.lower()

    def set_estado(self, estado: str) -> None:
        """Modifica el estado de la tarea."""
        self._estado = estado.lower()

    def set_google_event_id(self, event_id: str) -> None:
        """Establece el ID del evento en Google Calendar."""
        self._google_event_id = event_id

    # -------------------------------------------------------------------------
    # MÉTODOS ESPECIALES
    # -------------------------------------------------------------------------
    def __str__(self) -> str:
        """
        Representación en string de la tarea formateada.

        Returns:
            String con los datos de la tarea formateados para mostrar
        """
        # Iconos según prioridad
        icono_prioridad = {
            "alta": "🔴",
            "media": "🟡",
            "baja": "🟢"
        }.get(self._prioridad, "⚪")

        # Icono según estado
        icono_estado = "✅" if self._estado == "completada" else "⏳"

        # Icono de sincronización
        icono_sync = " 📅" if self._google_event_id else ""

        return (f"{icono_prioridad} {self._nombre}{icono_sync}\n"
                f"   📅 Fecha: {self._fecha_entrega}\n"
                f"   🏷️  Prioridad: {self._prioridad.upper()}\n"
                f"   {icono_estado} Estado: {self._estado.upper()}")

    def __repr__(self) -> str:
        """Representación oficial de la tarea."""
        return f"Tarea('{self._nombre}', '{self._fecha_entrega}', '{self._prioridad}', '{self._estado}')"

    # -------------------------------------------------------------------------
    # MÉTODOS DE SERIALIZACIÓN
    # -------------------------------------------------------------------------
    def to_dict(self) -> dict:
        """
        Convierte la tarea a un diccionario para serialización JSON.

        Returns:
            Diccionario con los atributos de la tarea
        """
        return {
            "nombre": self._nombre,
            "fecha_entrega": self._fecha_entrega,
            "prioridad": self._prioridad,
            "estado": self._estado,
            "google_event_id": self._google_event_id
        }

    @classmethod
    def from_dict(cls, datos: dict) -> "Tarea":
        """
        Crea una instancia de Tarea desde un diccionario.

        Args:
            datos: Diccionario con los datos de la tarea

        Returns:
            Nueva instancia de Tarea
        """
        return cls(
            nombre=datos["nombre"],
            fecha_entrega=datos["fecha_entrega"],
            prioridad=datos["prioridad"],
            estado=datos.get("estado", "pendiente"),
            google_event_id=datos.get("google_event_id")
        )


# =============================================================================
# INTEGRACIÓN CON GOOGLE CALENDAR
# =============================================================================
class GoogleCalendarSync:
    """
    Gestiona la sincronización de tareas con Google Calendar.

    Permite crear, actualizar y eliminar eventos en Google Calendar
    asociados a las tareas del sistema.
    """

    # Scopes necesarios para Google Calendar
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self):
        """Inicializa el gestor de sincronización."""
        self.service = None
        self.autenticado = False

    def autenticar(self) -> bool:
        """
        Autentica con Google Calendar usando las credenciales de Colab.
        Solicita los permisos necesarios (scopes) para crear/modificar eventos.

        Returns:
            True si la autenticación fue exitosa, False en caso contrario
        """
        if not GOOGLE_CALENDAR_AVAILABLE:
            Colores.print_colored("\n❌ Error: Las librerías de Google no están instaladas.", Colores.RED)
            print("   Ejecuta primero:")
            print("   !pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            return False

        try:
            Colores.print_colored("\n🔐 Autenticando con Google Calendar...", Colores.CYAN)
            print("   Se abrirá un enlace para autorizar el acceso.")
            print("   Asegúrate de conceder permisos para modificar tu calendario.\n")

            # En Google Colab, usar el flujo de autenticación estándar
            # que maneja los scopes automáticamente
            auth.authenticate_user()

            # Obtener credenciales con los scopes de Calendar
            # Después de autenticar, default() obtiene las credenciales con los scopes correctos
            creds, _ = default()

            # Verificar si tenemos los scopes necesarios
            if creds and creds.scopes:
                if not any('calendar' in scope for scope in creds.scopes):
                    Colores.print_colored("\n⚠️  Las credenciales no tienen permisos de Calendar.", Colores.YELLOW)
                    print("   Por favor, revoca el acceso previo y vuelve a autenticar:")
                    print("   1. Ve a: https://myaccount.google.com/permissions")
                    print("   2. Busca 'Google Colab' y haz clic en 'Quitar acceso'")
                    print("   3. Vuelve a ejecutar esta opción")
                    return False

            self.service = build('calendar', 'v3', credentials=creds)
            self.autenticado = True
            Colores.print_colored("✅ ¡Autenticación exitosa!", Colores.GREEN)
            print("   Ahora puedes crear y sincronizar eventos con Google Calendar.")
            return True
        except Exception as e:
            Colores.print_colored(f"\n❌ Error de autenticación: {e}", Colores.RED)
            print("\n⚠️  Si el error persiste, verifica que:")
            print("   1. Has habilitado Google Calendar API en tu proyecto de Google Cloud")
            print("   2. Concediste los permisos de 'Ver y editar eventos' en el calendario")
            print("   3. Has revocado accesos previos en: https://myaccount.google.com/permissions")
            return False

    def crear_evento(self, tarea: Tarea) -> Optional[str]:
        """
        Crea un evento en Google Calendar para una tarea.

        Args:
            tarea: Instancia de Tarea a sincronizar

        Returns:
            ID del evento creado o None si falla
        """
        if not self.autenticado or not self.service:
            Colores.print_colored("⚠️  No hay conexión con Google Calendar", Colores.YELLOW)
            return None

        try:
            # Asignar color según prioridad
            color_id = {
                'alta': '11',   # Rojo
                'media': '5',   # Amarillo
                'baja': '2'     # Verde
            }.get(tarea.get_prioridad(), '1')

            evento = {
                'summary': f"📚 {tarea.get_nombre()}",
                'description': f"Tarea académica - Prioridad: {tarea.get_prioridad().upper()}",
                'start': {
                    'date': tarea.get_fecha_entrega(),
                    'timeZone': 'America/Mexico_City',
                },
                'end': {
                    'date': tarea.get_fecha_entrega(),
                    'timeZone': 'America/Mexico_City',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 día antes
                        {'method': 'popup', 'minutes': 60},       # 1 hora antes
                    ],
                },
                'colorId': color_id,
            }

            resultado = self.service.events().insert(calendarId='primary', body=evento).execute()
            Colores.print_colored(f"✅ Evento creado en Google Calendar", Colores.GREEN)
            return resultado.get('id')

        except HttpError as e:
            Colores.print_colored(f"❌ Error al crear evento: {e}", Colores.RED)
            return None
        except Exception as e:
            Colores.print_colored(f"❌ Error inesperado: {e}", Colores.RED)
            return None

    def eliminar_evento(self, event_id: str) -> bool:
        """
        Elimina un evento de Google Calendar.

        Args:
            event_id: ID del evento a eliminar

        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        if not self.autenticado or not self.service or not event_id:
            return False

        try:
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            return True
        except Exception as e:
            print(f"⚠️  Error al eliminar evento: {e}")
            return False


# =============================================================================
# SISTEMA PRINCIPAL
# =============================================================================
class SistemaAcademico:
    """
    Sistema principal de administración de tareas.

    Gestiona la colección de tareas, su persistencia en JSON,
    la interfaz de usuario y la sincronización con Google Calendar.
    """

    ARCHIVO_TAREAS = "/content/tareas.json"

    def __init__(self):
        """Inicializa el sistema, cargando las tareas existentes."""
        self._tareas: List[Tarea] = []
        self._calendar = GoogleCalendarSync()
        self.cargar_tareas()

    # -------------------------------------------------------------------------
    # PERSISTENCIA
    # -------------------------------------------------------------------------
    def cargar_tareas(self) -> None:
        """
        Carga las tareas desde el archivo JSON.
        Si el archivo no existe o está corrupto, inicializa lista vacía.
        """
        try:
            if os.path.exists(self.ARCHIVO_TAREAS):
                with open(self.ARCHIVO_TAREAS, 'r', encoding='utf-8') as archivo:
                    datos = json.load(archivo)
                    self._tareas = [Tarea.from_dict(t) for t in datos]
                Colores.print_colored(f"✓ Se cargaron {len(self._tareas)} tarea(s)", Colores.GREEN)
            else:
                print("✓ No hay tareas previas. Comenzando con lista vacía.")
        except json.JSONDecodeError:
            Colores.print_colored("⚠️  El archivo de tareas está corrupto. Se inicia con lista vacía.", Colores.YELLOW)
            self._tareas = []
        except Exception as e:
            Colores.print_colored(f"⚠️  Error al cargar: {e}", Colores.YELLOW)
            self._tareas = []

    def guardar_tareas(self) -> None:
        """Guarda todas las tareas en el archivo JSON."""
        try:
            with open(self.ARCHIVO_TAREAS, 'w', encoding='utf-8') as archivo:
                json.dump([t.to_dict() for t in self._tareas], archivo, indent=2, ensure_ascii=False)
        except Exception as e:
            Colores.print_colored(f"❌ Error al guardar: {e}", Colores.RED)

    # -------------------------------------------------------------------------
    # VALIDACIONES
    # -------------------------------------------------------------------------
    @staticmethod
    def validar_fecha(fecha: str) -> bool:
        """
        Valida que la fecha tenga el formato correcto YYYY-MM-DD.

        Args:
            fecha: String con la fecha a validar

        Returns:
            True si es válida, False en caso contrario
        """
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    @staticmethod
    def validar_prioridad(prioridad: str) -> bool:
        """
        Valida que la prioridad sea una de las opciones permitidas.

        Args:
            prioridad: String con la prioridad a validar

        Returns:
            True si es válida, False en caso contrario
        """
        return prioridad.lower() in ["alta", "media", "baja"]

    def validar_indice(self, indice: int) -> bool:
        """
        Valida que el índice de tarea exista en la lista.

        Args:
            indice: Número de tarea (1-based)

        Returns:
            True si existe, False en caso contrario
        """
        return 1 <= indice <= len(self._tareas)

    # -------------------------------------------------------------------------
    # OPERACIONES CRUD
    # -------------------------------------------------------------------------
    def agregar_tarea(self, nombre: str, fecha: str, prioridad: str,
                      sync_calendar: bool = False) -> None:
        """
        Agrega una nueva tarea al sistema.

        Args:
            nombre: Nombre de la tarea
            fecha: Fecha en formato YYYY-MM-DD
            prioridad: Prioridad (alta, media, baja)
            sync_calendar: Si es True, sincroniza con Google Calendar

        Raises:
            ValueError: Si alguna validación falla
        """
        # Validaciones
        if not nombre or not nombre.strip():
            raise ValueError("El nombre de la tarea no puede estar vacío")

        if not self.validar_fecha(fecha):
            raise ValueError("La fecha debe tener el formato YYYY-MM-DD (ej: 2024-12-31)")

        if not self.validar_prioridad(prioridad):
            raise ValueError('La prioridad debe ser "alta", "media" o "baja"')

        # Crear tarea
        tarea = Tarea(nombre.strip(), fecha, prioridad.lower())

        # Sincronizar con Google Calendar si se solicita
        if sync_calendar:
            if not self._calendar.autenticado:
                print("\n⚠️  Debes autenticar con Google Calendar primero (opción 8)")
            else:
                event_id = self._calendar.crear_evento(tarea)
                if event_id:
                    tarea.set_google_event_id(event_id)

        self._tareas.append(tarea)
        self.guardar_tareas()
        Colores.print_colored(f"\n✅ Tarea agregada: '{nombre}'", Colores.GREEN)

    def ver_tareas(self, filtro: str = "todas") -> None:
        """
        Muestra las tareas con opción de filtrado.

        Args:
            filtro: Tipo de filtro ("todas", "pendientes", "completadas",
                   "alta", "media", "baja")
        """
        tareas_mostrar = self._tareas

        # Aplicar filtros
        if filtro == "pendientes":
            tareas_mostrar = [t for t in self._tareas if t.get_estado() == "pendiente"]
        elif filtro == "completadas":
            tareas_mostrar = [t for t in self._tareas if t.get_estado() == "completada"]
        elif filtro in ["alta", "media", "baja"]:
            tareas_mostrar = [t for t in self._tareas if t.get_prioridad() == filtro]

        if not tareas_mostrar:
            print(f"\n📭 No hay tareas {filtro}.")
            return

        print("\n" + "=" * 60)
        print(f"📋 LISTA DE TAREAS ({filtro.upper()})")
        print("=" * 60)

        for i, tarea in enumerate(tareas_mostrar, 1):
            # Encontrar índice real en la lista completa
            idx_real = self._tareas.index(tarea) + 1
            print(f"\n[{idx_real}]")
            print(tarea)
            print("-" * 50)

        print(f"\nTotal mostradas: {len(tareas_mostrar)}")

    def marcar_completada(self, numero: int) -> None:
        """
        Marca una tarea como completada.

        Args:
            numero: Número de la tarea (1-based)

        Raises:
            ValueError: Si el número de tarea no existe
        """
        if not self.validar_indice(numero):
            raise ValueError(f"La tarea #{numero} no existe. Hay {len(self._tareas)} tarea(s).")

        tarea = self._tareas[numero - 1]

        if tarea.get_estado() == "completada":
            print(f"\n⚠️  La tarea '{tarea.get_nombre()}' ya está completada.")
        else:
            tarea.set_estado("completada")
            self.guardar_tareas()
            Colores.print_colored(f"\n✅ Tarea '{tarea.get_nombre()}' marcada como completada", Colores.GREEN)

    def eliminar_tarea(self, numero: int) -> None:
        """
        Elimina una tarea del sistema.

        Args:
            numero: Número de la tarea a eliminar (1-based)

        Raises:
            ValueError: Si el número de tarea no existe
        """
        if not self.validar_indice(numero):
            raise ValueError(f"La tarea #{numero} no existe. Hay {len(self._tareas)} tarea(s).")

        tarea = self._tareas[numero - 1]

        # Eliminar de Google Calendar si tiene evento asociado
        if tarea.get_google_event_id():
            self._calendar.eliminar_evento(tarea.get_google_event_id())

        nombre = tarea.get_nombre()
        del self._tareas[numero - 1]
        self.guardar_tareas()
        Colores.print_colored(f"\n🗑️  Tarea '{nombre}' eliminada", Colores.GREEN)

    def ordenar_por_fecha(self) -> None:
        """Ordena las tareas por fecha de entrega (más próxima primero)."""
        if not self._tareas:
            print("\n📭 No hay tareas para ordenar.")
            return

        self._tareas.sort(key=lambda t: t.get_fecha_entrega())
        self.guardar_tareas()
        Colores.print_colored("\n✅ Tareas ordenadas por fecha de entrega", Colores.GREEN)
        self.ver_tareas("todas")

    def buscar_tareas(self, termino: str) -> List[Tarea]:
        """
        Busca tareas por nombre (búsqueda parcial, case-insensitive).

        Args:
            termino: Término de búsqueda

        Returns:
            Lista de tareas que coinciden
        """
        termino_lower = termino.lower()
        return [t for t in self._tareas if termino_lower in t.get_nombre().lower()]

    # -------------------------------------------------------------------------
    # ALERTAS Y ESTADÍSTICAS
    # -------------------------------------------------------------------------
    def mostrar_alertas(self) -> None:
        """Muestra alertas de tareas próximas a vencer o vencidas."""
        hoy = datetime.now().date()
        alertas = []

        for tarea in self._tareas:
            if tarea.get_estado() == "pendiente":
                fecha = datetime.strptime(tarea.get_fecha_entrega(), "%Y-%m-%d").date()
                dias = (fecha - hoy).days

                if dias <= 3:
                    alertas.append((tarea, dias))

        if alertas:
            print("\n" + "🚨" * 25)
            Colores.print_colored("⚠️  ALERTAS DE TAREAS URGENTES", Colores.YELLOW)
            print("🚨" * 25)

            for tarea, dias in sorted(alertas, key=lambda x: x[1]):
                if dias < 0:
                    mensaje = f"🔴 VENCIDA hace {abs(dias)} día(s)"
                    color = Colores.RED
                elif dias == 0:
                    mensaje = "🔴 VENCE HOY"
                    color = Colores.RED
                elif dias == 1:
                    mensaje = "🟠 Vence mañana"
                    color = Colores.YELLOW
                else:
                    mensaje = f"🟡 Vence en {dias} días"
                    color = Colores.CYAN

                print(f"\n   • {tarea.get_nombre()}")
                Colores.print_colored(f"     {mensaje} ({tarea.get_fecha_entrega()})", color)
        else:
            Colores.print_colored("\n✅ No hay alertas. ¡Todo en orden!", Colores.GREEN)

    def verificar_alertas_inicio(self) -> None:
        """Verifica y muestra alertas al iniciar el programa."""
        if not self._tareas:
            return

        hoy = datetime.now().date()
        vencidas = 0
        proximas = 0

        for tarea in self._tareas:
            if tarea.get_estado() == "pendiente":
                fecha = datetime.strptime(tarea.get_fecha_entrega(), "%Y-%m-%d").date()
                dias = (fecha - hoy).days

                if dias < 0:
                    vencidas += 1
                elif dias <= 3:
                    proximas += 1

        if vencidas > 0 or proximas > 0:
            print("\n" + "⚠️" * 20)
            print("   🔔 NOTIFICACIONES:")
            if vencidas > 0:
                Colores.print_colored(f"   🔴 {vencidas} tarea(s) VENCIDA(S)!", Colores.RED)
            if proximas > 0:
                Colores.print_colored(f"   🟡 {proximas} tarea(s) próximas a vencer", Colores.YELLOW)
            print("⚠️" * 20)

    def ver_estadisticas(self) -> None:
        """Muestra estadísticas del sistema."""
        total = len(self._tareas)

        if total == 0:
            print("\n📊 No hay tareas para estadísticas.")
            return

        completadas = sum(1 for t in self._tareas if t.get_estado() == "completada")
        pendientes = total - completadas
        productividad = (completadas / total) * 100

        prioridades = {
            'alta': sum(1 for t in self._tareas if t.get_prioridad() == 'alta'),
            'media': sum(1 for t in self._tareas if t.get_prioridad() == 'media'),
            'baja': sum(1 for t in self._tareas if t.get_prioridad() == 'baja')
        }

        print("\n" + "=" * 50)
        Colores.print_colored("📊 ESTADÍSTICAS DEL SISTEMA", Colores.CYAN)
        print("=" * 50)
        print(f"   📁 Total de tareas:      {total}")
        Colores.print_colored(f"   ✅ Completadas:          {completadas}", Colores.GREEN)
        Colores.print_colored(f"   ⏳ Pendientes:           {pendientes}", Colores.YELLOW)

        # Barra de productividad
        barra = "█" * int(productividad / 5) + "░" * (20 - int(productividad / 5))
        color_prod = Colores.GREEN if productividad >= 70 else Colores.YELLOW if productividad >= 40 else Colores.RED
        print(f"\n   📈 Productividad:        {productividad:.1f}%")
        Colores.print_colored(f"   [{barra}]", color_prod)

        print(f"\n   🔴 Prioridad Alta:       {prioridades['alta']}")
        print(f"   🟡 Prioridad Media:      {prioridades['media']}")
        print(f"   🟢 Prioridad Baja:       {prioridades['baja']}")
        print("=" * 50)

    # -------------------------------------------------------------------------
    # GOOGLE CALENDAR
    # -------------------------------------------------------------------------
    def autenticar_google_calendar(self) -> bool:
        """Autentica con Google Calendar."""
        return self._calendar.autenticar()

    def sincronizar_todas_con_calendar(self) -> None:
        """Sincroniza todas las tareas pendientes con Google Calendar."""
        if not self._calendar.autenticado:
            Colores.print_colored("\n❌ Debes autenticar con Google Calendar primero (opción 8)", Colores.RED)
            return

        tareas_pendientes = [t for t in self._tareas
                            if t.get_estado() == "pendiente" and not t.get_google_event_id()]

        if not tareas_pendientes:
            print("\n📭 No hay tareas pendientes para sincronizar.")
            return

        print(f"\n🔄 Sincronizando {len(tareas_pendientes)} tarea(s)...")

        sincronizadas = 0
        for tarea in tareas_pendientes:
            event_id = self._calendar.crear_evento(tarea)
            if event_id:
                tarea.set_google_event_id(event_id)
                sincronizadas += 1

        self.guardar_tareas()
        Colores.print_colored(f"✅ {sincronizadas} tarea(s) sincronizada(s) con Google Calendar", Colores.GREEN)


# =============================================================================
# INTERFAZ DE USUARIO (MENÚ)
# =============================================================================
def mostrar_banner():
    """Muestra el banner de bienvenida."""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║        📚 SISTEMA ACADÉMICO DE TAREAS 📚                 ║
    ║              con Google Calendar Sync                    ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    Colores.print_colored(banner, Colores.CYAN)


def mostrar_menu():
    """Muestra el menú principal."""
    print("\n" + "=" * 60)
    Colores.print_colored("📋 MENÚ PRINCIPAL", Colores.CYAN)
    print("=" * 60)
    print("""
   [1] ➕  Agregar nueva tarea
   [2] 📋 Ver todas las tareas
   [3] ✔️   Marcar tarea como completada
   [4] 🗑️   Eliminar tarea
   [5] 📅 Ordenar tareas por fecha
   [6] 🚨 Mostrar alertas de vencimiento
   [7] 📊 Ver estadísticas
   [8] 📅 Sincronizar con Google Calendar
   [9] 🚪 Salir y guardar
    """)
    print("=" * 60)


def submenu_filtros(sistema: SistemaAcademico):
    """Submenú para filtros de tareas."""
    while True:
        print("\n" + "-" * 40)
        print("🔍 FILTRAR TAREAS")
        print("-" * 40)
        print("   [1] Todas")
        print("   [2] Pendientes")
        print("   [3] Completadas")
        print("   [4] Prioridad Alta")
        print("   [5] Prioridad Media")
        print("   [6] Prioridad Baja")
        print("   [7] Buscar por nombre")
        print("   [0] Volver al menú principal")

        try:
            opcion = input("\n👉 Opción: ").strip()

            if opcion == "1":
                sistema.ver_tareas("todas")
            elif opcion == "2":
                sistema.ver_tareas("pendientes")
            elif opcion == "3":
                sistema.ver_tareas("completadas")
            elif opcion == "4":
                sistema.ver_tareas("alta")
            elif opcion == "5":
                sistema.ver_tareas("media")
            elif opcion == "6":
                sistema.ver_tareas("baja")
            elif opcion == "7":
                termino = input("\n🔍 Término de búsqueda: ").strip()
                resultados = sistema.buscar_tareas(termino)
                if resultados:
                    print(f"\n✅ Se encontraron {len(resultados)} resultado(s):")
                    for t in resultados:
                        print(f"\n[{sistema._tareas.index(t) + 1}]")
                        print(t)
                else:
                    print("\n❌ No se encontraron tareas.")
            elif opcion == "0":
                break
            else:
                print("❌ Opción inválida")

        except Exception as e:
            Colores.print_colored(f"❌ Error: {e}", Colores.RED)


def main():
    """Función principal del sistema."""
    # Limpiar pantalla (compatible con Colab)
    try:
        from IPython.display import clear_output
        clear_output(wait=True)
    except:
        pass

    mostrar_banner()

    # Crear instancia del sistema
    sistema = SistemaAcademico()

    # Mostrar alertas al iniciar
    sistema.verificar_alertas_inicio()

    # Bucle principal
    ejecutando = True
    while ejecutando:
        mostrar_menu()

        try:
            opcion = input("\n👉 Seleccione una opción (1-9): ").strip()

            if opcion == "1":  # Agregar tarea
                print("\n" + "-" * 40)
                Colores.print_colored("➕ AGREGAR NUEVA TAREA", Colores.CYAN)
                print("-" * 40)

                nombre = input("\n📝 Nombre de la tarea: ").strip()
                fecha = input("📅 Fecha de entrega (YYYY-MM-DD): ").strip()
                print("\n🏷️  Prioridades disponibles:")
                print("   🔴 alta | 🟡 media | 🟢 baja")
                prioridad = input("👉 Prioridad: ").strip()

                sync = input("\n¿Sincronizar con Google Calendar? (s/n): ").strip().lower() == 's'

                sistema.agregar_tarea(nombre, fecha, prioridad, sync)

            elif opcion == "2":  # Ver tareas
                submenu_filtros(sistema)

            elif opcion == "3":  # Marcar completada
                sistema.ver_tareas("todas")
                if sistema._tareas:
                    try:
                        num = int(input("\n👉 Número de tarea a completar: "))
                        sistema.marcar_completada(num)
                    except ValueError:
                        print("❌ Debes ingresar un número válido")

            elif opcion == "4":  # Eliminar tarea
                sistema.ver_tareas("todas")
                if sistema._tareas:
                    try:
                        num = int(input("\n👉 Número de tarea a eliminar: "))
                        confirmar = input(f"⚠️  ¿Estás seguro? (s/n): ").strip().lower()
                        if confirmar == 's':
                            sistema.eliminar_tarea(num)
                    except ValueError:
                        print("❌ Debes ingresar un número válido")

            elif opcion == "5":  # Ordenar por fecha
                sistema.ordenar_por_fecha()

            elif opcion == "6":  # Mostrar alertas
                sistema.mostrar_alertas()

            elif opcion == "7":  # Estadísticas
                sistema.ver_estadisticas()

            elif opcion == "8":  # Sincronizar con Google Calendar
                print("\n" + "-" * 40)
                Colores.print_colored("📅 GOOGLE CALENDAR SYNC", Colores.CYAN)
                print("-" * 40)
                print("\n   [1] 🔐 Autenticar con Google")
                print("   [2] 🔄 Sincronizar todas las tareas pendientes")

                subopcion = input("\n👉 Opción: ").strip()

                if subopcion == "1":
                    sistema.autenticar_google_calendar()
                elif subopcion == "2":
                    sistema.sincronizar_todas_con_calendar()
                else:
                    print("❌ Opción inválida")

            elif opcion == "9":  # Salir
                print("\n💾 Guardando tareas...")
                sistema.guardar_tareas()
                Colores.print_colored("\n✅ ¡Hasta luego! 👋", Colores.GREEN)
                ejecutando = False

            else:
                Colores.print_colored("\n❌ Opción inválida. Usa 1-9.", Colores.RED)

        except ValueError as e:
            Colores.print_colored(f"\n❌ Error: {e}", Colores.RED)
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupción detectada. Guardando...")
            sistema.guardar_tareas()
            break
        except Exception as e:
            Colores.print_colored(f"\n❌ Error inesperado: {e}", Colores.RED)


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================
if __name__ == "__main__":
    main()
