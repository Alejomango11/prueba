#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Académico de Administración de Tareas - Versión Google Colab
====================================================================
Versión especial para Google Colab con integración completa a Google Calendar.
Permite sincronizar automáticamente las tareas con el calendario del usuario.

Instrucciones de uso en Colab:
1. Ejecutar la celda de instalación de dependencias
2. Ejecutar este script
3. Autorizar el acceso a Google Calendar cuando se solicite
4. Usar el menú interactivo
"""

# =============================================================================
# INSTALACIÓN DE DEPENDENCIAS (ejecutar primero en Colab)
# =============================================================================
# Copia y pega esto en una celda separada antes de ejecutar el script:
"""
!pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
"""

import json
import os
import pickle
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from google.colab import auth
from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# =============================================================================
# CLASE PRINCIPAL: TAREA
# =============================================================================
class Tarea:
    """
    Representa una tarea académica con sus atributos y métodos asociados.
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

    # Getters
    def get_nombre(self) -> str:
        return self._nombre

    def get_fecha_entrega(self) -> str:
        return self._fecha_entrega

    def get_prioridad(self) -> str:
        return self._prioridad

    def get_estado(self) -> str:
        return self._estado

    def get_google_event_id(self) -> Optional[str]:
        return self._google_event_id

    # Setters
    def set_nombre(self, nombre: str) -> None:
        self._nombre = nombre

    def set_fecha_entrega(self, fecha_entrega: str) -> None:
        self._fecha_entrega = fecha_entrega

    def set_prioridad(self, prioridad: str) -> None:
        self._prioridad = prioridad.lower()

    def set_estado(self, estado: str) -> None:
        self._estado = estado.lower()

    def set_google_event_id(self, event_id: str) -> None:
        self._google_event_id = event_id

    def __str__(self) -> str:
        """Representación en string de la tarea formateada."""
        icono_prioridad = {"alta": "🔴", "media": "🟡", "baja": "🟢"}.get(self._prioridad, "⚪")
        icono_estado = "✅" if self._estado == "completada" else "⏳"
        sync_icon = "📅" if self._google_event_id else ""

        return (f"{icono_prioridad} {self._nombre} {sync_icon}\n"
                f"   📅 Fecha de entrega: {self._fecha_entrega}\n"
                f"   🏷️  Prioridad: {self._prioridad.upper()}\n"
                f"   {icono_estado} Estado: {self._estado.upper()}")

    def to_dict(self) -> dict:
        """Convierte la tarea a un diccionario para serialización JSON."""
        return {
            "nombre": self._nombre,
            "fecha_entrega": self._fecha_entrega,
            "prioridad": self._prioridad,
            "estado": self._estado,
            "google_event_id": self._google_event_id
        }

    @classmethod
    def from_dict(cls, datos: dict) -> "Tarea":
        """Crea una instancia de Tarea desde un diccionario."""
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
    Gestiona la sincronización con Google Calendar.
    """

    def __init__(self):
        self.service = None
        self.autenticado = False

    def autenticar(self) -> bool:
        """
        Autentica con Google usando las credenciales de Colab.
        Retorna True si la autenticación fue exitosa.
        """
        try:
            print("🔐 Autenticando con Google...")
            auth.authenticate_user()
            creds, _ = default()
            self.service = build('calendar', 'v3', credentials=creds)
            self.autenticado = True
            print("✅ Autenticación exitosa con Google Calendar!")
            return True
        except Exception as e:
            print(f"❌ Error de autenticación: {e}")
            return False

    def crear_evento(self, tarea: Tarea) -> Optional[str]:
        """
        Crea un evento en Google Calendar para la tarea.

        Returns:
            ID del evento creado o None si falla
        """
        if not self.autenticado:
            print("⚠️  No hay autenticación con Google Calendar")
            return None

        try:
            # Determinar color según prioridad
            color_id = {
                'alta': '11',   # Rojo
                'media': '5',   # Amarillo
                'baja': '2'     # Verde
            }.get(tarea.get_prioridad(), '1')

            fecha = tarea.get_fecha_entrega()

            evento = {
                'summary': f"📚 {tarea.get_nombre()}",
                'description': f"Tarea académica - Prioridad: {tarea.get_prioridad().upper()}",
                'start': {
                    'date': fecha,
                    'timeZone': 'America/Mexico_City',
                },
                'end': {
                    'date': fecha,
                    'timeZone': 'America/Mexico_City',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 60},
                    ],
                },
                'colorId': color_id,
            }

            resultado = self.service.events().insert(calendarId='primary', body=evento).execute()
            print(f"📅 Evento creado en Google Calendar: {resultado.get('htmlLink')}")
            return resultado.get('id')

        except HttpError as e:
            print(f"❌ Error al crear evento: {e}")
            return None
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return None

    def eliminar_evento(self, event_id: str) -> bool:
        """Elimina un evento de Google Calendar."""
        if not self.autenticado or not event_id:
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
class SistemaTareas:
    """
    Sistema principal que gestiona la colección de tareas.
    """

    ARCHIVO_TAREAS = "/content/tareas.json"

    def __init__(self):
        self._tareas: List[Tarea] = []
        self.calendar = GoogleCalendarSync()
        self.cargar_tareas()

    def cargar_tareas(self) -> None:
        """Carga las tareas desde el archivo JSON."""
        try:
            from google.colab import files
            if os.path.exists(self.ARCHIVO_TAREAS):
                with open(self.ARCHIVO_TAREAS, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                    self._tareas = [Tarea.from_dict(t) for t in datos]
                print(f"✓ Se cargaron {len(self._tareas)} tarea(s).")
            else:
                print("✓ No hay tareas previas. Comenzando con lista vacía.")
        except Exception as e:
            print(f"⚠️  Error al cargar: {e}")
            self._tareas = []

    def guardar_tareas(self) -> None:
        """Guarda las tareas en el archivo JSON."""
        try:
            with open(self.ARCHIVO_TAREAS, 'w', encoding='utf-8') as f:
                json.dump([t.to_dict() for t in self._tareas], f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error al guardar: {e}")

    def autenticar_google_calendar(self) -> bool:
        """Inicia la autenticación con Google Calendar."""
        return self.calendar.autenticar()

    def agregar_tarea(self, nombre: str, fecha_entrega: str, prioridad: str,
                      sync_calendar: bool = False) -> None:
        """
        Agrega una nueva tarea con validaciones.

        Args:
            nombre: Nombre de la tarea
            fecha_entrega: Fecha en formato YYYY-MM-DD
            prioridad: alta, media o baja
            sync_calendar: Si es True, sincroniza con Google Calendar
        """
        # Validar fecha
        try:
            datetime.strptime(fecha_entrega, "%Y-%m-%d")
        except ValueError:
            raise ValueError("La fecha debe tener el formato YYYY-MM-DD")

        # Validar prioridad
        if prioridad.lower() not in ["alta", "media", "baja"]:
            raise ValueError('La prioridad debe ser "alta", "media" o "baja"')

        # Crear tarea
        tarea = Tarea(nombre, fecha_entrega, prioridad)

        # Sincronizar con Google Calendar si se solicita
        if sync_calendar and self.calendar.autenticado:
            event_id = self.calendar.crear_evento(tarea)
            if event_id:
                tarea.set_google_event_id(event_id)

        self._tareas.append(tarea)
        self.guardar_tareas()
        print(f"\n✅ Tarea agregada: '{nombre}'")

    def ver_todas_tareas(self) -> None:
        """Muestra todas las tareas numeradas."""
        if not self._tareas:
            print("\n📭 No hay tareas registradas.")
            return

        print("\n" + "=" * 50)
        print("📋 LISTA DE TAREAS")
        print("=" * 50)

        for i, tarea in enumerate(self._tareas, 1):
            print(f"\n[{i}]")
            print(tarea)
            print("-" * 40)

    def marcar_completada(self, numero_tarea: int) -> None:
        """Marca una tarea como completada."""
        if not 1 <= numero_tarea <= len(self._tareas):
            raise ValueError(f"La tarea #{numero_tarea} no existe.")

        tarea = self._tareas[numero_tarea - 1]

        if tarea.get_estado() == "completada":
            print(f"\n⚠️  La tarea '{tarea.get_nombre()}' ya está completada.")
        else:
            tarea.set_estado("completada")
            self.guardar_tareas()
            print(f"\n✅ Tarea '{tarea.get_nombre()}' marcada como completada.")

    def eliminar_tarea(self, numero_tarea: int) -> None:
        """Elimina una tarea del sistema."""
        if not 1 <= numero_tarea <= len(self._tareas):
            raise ValueError(f"La tarea #{numero_tarea} no existe.")

        tarea = self._tareas[numero_tarea - 1]

        # Eliminar de Google Calendar si tiene evento asociado
        if tarea.get_google_event_id():
            self.calendar.eliminar_evento(tarea.get_google_event_id())

        del self._tareas[numero_tarea - 1]
        self.guardar_tareas()
        print(f"\n🗑️  Tarea '{tarea.get_nombre()}' eliminada.")

    def ver_tareas_ordenadas(self) -> None:
        """Muestra tareas ordenadas por fecha de entrega."""
        if not self._tareas:
            print("\n📭 No hay tareas registradas.")
            return

        tareas_ordenadas = sorted(self._tareas, key=lambda t: t.get_fecha_entrega())

        print("\n" + "=" * 50)
        print("📅 TAREAS ORDENADAS POR FECHA")
        print("=" * 50)

        for i, tarea in enumerate(tareas_ordenadas, 1):
            fecha = datetime.strptime(tarea.get_fecha_entrega(), "%Y-%m-%d").date()
            hoy = datetime.now().date()
            dias = (fecha - hoy).days

            indicador = "🟢"
            if tarea.get_estado() == "completada":
                indicador = "✅"
            elif dias < 0:
                indicador = "🔴 VENCIDA"
            elif dias == 0:
                indicador = "🔴 HOY"
            elif dias <= 3:
                indicador = "🟡 URGENTE"

            print(f"\n[{i}] {indicador}")
            print(tarea)

    def mostrar_alertas(self) -> None:
        """Muestra alertas de tareas próximas a vencer."""
        hoy = datetime.now().date()
        alertas = []

        for tarea in self._tareas:
            if tarea.get_estado() == "pendiente":
                fecha = datetime.strptime(tarea.get_fecha_entrega(), "%Y-%m-%d").date()
                dias = (fecha - hoy).days

                if dias <= 3:
                    alertas.append((tarea, dias))

        if alertas:
            print("\n" + "🚨" * 20)
            print("⚠️  ALERTAS DE TAREAS URGENTES")
            print("🚨" * 20)

            for tarea, dias in alertas:
                if dias < 0:
                    mensaje = f"🔴 VENCIDA hace {abs(dias)} día(s)"
                elif dias == 0:
                    mensaje = "🔴 VENCE HOY"
                elif dias == 1:
                    mensaje = "🟠 Vence mañana"
                else:
                    mensaje = f"🟡 Vence en {dias} días"

                print(f"\n   • {tarea.get_nombre()}")
                print(f"     {mensaje} ({tarea.get_fecha_entrega()})")
        else:
            print("\n✅ No hay alertas. Todo en orden!")

    def verificar_alertas_inicio(self) -> None:
        """Verifica alertas al iniciar el programa."""
        if not self._tareas:
            return

        hoy = datetime.now().date()
        vencidas = sum(
            1 for t in self._tareas
            if t.get_estado() == "pendiente"
            and (datetime.strptime(t.get_fecha_entrega(), "%Y-%m-%d").date() - hoy).days < 0
        )
        proximas = sum(
            1 for t in self._tareas
            if t.get_estado() == "pendiente"
            and 0 <= (datetime.strptime(t.get_fecha_entrega(), "%Y-%m-%d").date() - hoy).days <= 3
        )

        if vencidas > 0 or proximas > 0:
            print("\n" + "⚠️" * 20)
            if vencidas > 0:
                print(f"   🔴 {vencidas} tarea(s) VENCIDA(S)!")
            if proximas > 0:
                print(f"   🟡 {proximas} tarea(s) próximas a vencer")
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

        alta = sum(1 for t in self._tareas if t.get_prioridad() == "alta")
        media = sum(1 for t in self._tareas if t.get_prioridad() == "media")
        baja = sum(1 for t in self._tareas if t.get_prioridad() == "baja")

        print("\n" + "=" * 50)
        print("📊 ESTADÍSTICAS")
        print("=" * 50)
        print(f"   📁 Total: {total}")
        print(f"   ✅ Completadas: {completadas}")
        print(f"   ⏳ Pendientes: {pendientes}")
        print(f"   📈 Productividad: {productividad:.1f}%")
        print(f"\n   🔴 Alta: {alta} | 🟡 Media: {media} | 🟢 Baja: {baja}")


# =============================================================================
# MENÚ INTERACTIVO
# =============================================================================
def mostrar_menu():
    """Muestra el menú principal."""
    print("\n" + "=" * 50)
    print("📚 SISTEMA ACADÉMICO DE TAREAS")
    print("   con Google Calendar Integration")
    print("=" * 50)
    print("\n   [1] ➕ Agregar tarea")
    print("   [2] 📋 Ver todas las tareas")
    print("   [3] ✔️  Marcar como completada")
    print("   [4] 🗑️  Eliminar tarea")
    print("   [5] 📅 Ver ordenadas por fecha")
    print("   [6] 🚨 Mostrar alertas")
    print("   [7] 📊 Ver estadísticas")
    print("   [8] 🔗 Conectar Google Calendar")
    print("   [9] 🚪 Salir")


def main():
    """Función principal."""
    from IPython.display import clear_output
    clear_output(wait=True)

    print("\n🎓" * 20)
    print("   SISTEMA ACADÉMICO DE TAREAS")
    print("   Versión Google Colab + Calendar")
    print("🎓" * 20)

    sistema = SistemaTareas()
    sistema.verificar_alertas_inicio()

    ejecutando = True
    while ejecutando:
        mostrar_menu()

        try:
            opcion = int(input("\n👉 Opción (1-9): ").strip())

            if opcion == 1:
                print("\n--- Agregar Tarea ---")
                nombre = input("Nombre: ").strip()
                fecha = input("Fecha (YYYY-MM-DD): ").strip()
                print("Prioridad: alta / media / baja")
                prioridad = input("Prioridad: ").strip()

                sync = input("¿Sincronizar con Google Calendar? (s/n): ").strip().lower() == 's'

                if sync and not sistema.calendar.autenticado:
                    print("\nPrimero debes autenticar con Google Calendar (opción 8)")
                    sync = False

                sistema.agregar_tarea(nombre, fecha, prioridad, sync)

            elif opcion == 2:
                sistema.ver_todas_tareas()

            elif opcion == 3:
                sistema.ver_todas_tareas()
                num = int(input("\nNúmero de tarea a completar: "))
                sistema.marcar_completada(num)

            elif opcion == 4:
                sistema.ver_todas_tareas()
                num = int(input("\nNúmero de tarea a eliminar: "))
                confirmar = input(f"¿Seguro? (s/n): ").strip().lower()
                if confirmar == 's':
                    sistema.eliminar_tarea(num)

            elif opcion == 5:
                sistema.ver_tareas_ordenadas()

            elif opcion == 6:
                sistema.mostrar_alertas()

            elif opcion == 7:
                sistema.ver_estadisticas()

            elif opcion == 8:
                sistema.autenticar_google_calendar()

            elif opcion == 9:
                print("\n💾 Guardando...")
                sistema.guardar_tareas()
                print("✅ ¡Hasta luego!")
                ejecutando = False

            else:
                print("❌ Opción inválida. Use 1-9.")

        except ValueError as e:
            print(f"\n❌ Error: {e}")
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")


# Iniciar el sistema
main()
