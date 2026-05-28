#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Académico de Administración de Tareas - Web App
==========================================================
Aplicación web Flask con integración a Google Calendar API.
Permite gestionar tareas y sincronizarlas automáticamente con Google Calendar.
"""

import os
import json
import pickle
from datetime import datetime, timedelta
from functools import wraps
from typing import List, Dict, Optional

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_cors import CORS

# Google Calendar API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    GOOGLE_CALENDAR_AVAILABLE = False
    print("Advertencia: google-api-python-client no instalado. La integración con Google Calendar no estará disponible.")

# Importar el sistema de tareas existente
from sistema_academico_tareas import Tarea, SistemaTareas

# Configuración de la aplicación
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave-secreta-desarrollo-cambiar-en-produccion')
CORS(app)

# Configuración de Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']
CLIENT_SECRETS_FILE = 'client_secrets.json'
TOKEN_FILE = 'token.pickle'

# ============================================================================
# CLASE EXTENDIDA: Tarea con soporte para Google Calendar
# ============================================================================
class TareaCalendar(Tarea):
    """
    Extensión de la clase Tarea con soporte para Google Calendar.
    """

    def __init__(self, nombre: str, fecha_entrega: str, prioridad: str,
                 estado: str = "pendiente", google_event_id: str = None):
        super().__init__(nombre, fecha_entrega, prioridad, estado)
        self._google_event_id = google_event_id

    def get_google_event_id(self) -> Optional[str]:
        return self._google_event_id

    def set_google_event_id(self, event_id: str) -> None:
        self._google_event_id = event_id

    def to_dict(self) -> dict:
        data = super().to_dict()
        data['google_event_id'] = self._google_event_id
        return data

    @classmethod
    def from_dict(cls, datos: dict) -> "TareaCalendar":
        return cls(
            nombre=datos["nombre"],
            fecha_entrega=datos["fecha_entrega"],
            prioridad=datos["prioridad"],
            estado=datos.get("estado", "pendiente"),
            google_event_id=datos.get("google_event_id")
        )


# ============================================================================
# GESTOR DE GOOGLE CALENDAR
# ============================================================================
class GoogleCalendarManager:
    """
    Gestiona la integración con Google Calendar API.
    """

    def __init__(self):
        self.service = None
        self.credentials = None

    def load_credentials(self) -> bool:
        """
        Carga las credenciales guardadas o retorna False si no existen.
        """
        if not GOOGLE_CALENDAR_AVAILABLE:
            return False

        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                self.credentials = pickle.load(token)

        # Si no hay credenciales válidas, retornar False
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                try:
                    self.credentials.refresh(Request())
                    # Guardar credenciales actualizadas
                    with open(TOKEN_FILE, 'wb') as token:
                        pickle.dump(self.credentials, token)
                except Exception as e:
                    print(f"Error al refrescar token: {e}")
                    return False
            else:
                return False

        # Crear el servicio de Google Calendar
        try:
            self.service = build('calendar', 'v3', credentials=self.credentials)
            return True
        except Exception as e:
            print(f"Error al crear servicio: {e}")
            return False

    def get_auth_url(self) -> str:
        """
        Genera la URL de autorización de Google OAuth2.
        """
        if not GOOGLE_CALENDAR_AVAILABLE:
            raise Exception("Google Calendar API no disponible")

        if not os.path.exists(CLIENT_SECRETS_FILE):
            raise Exception(f"Archivo {CLIENT_SECRETS_FILE} no encontrado. Descárgalo desde Google Cloud Console.")

        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=url_for('oauth2callback', _external=True)
        )

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        session['state'] = state
        return authorization_url

    def handle_callback(self, authorization_response: str) -> bool:
        """
        Maneja el callback de OAuth2 y guarda las credenciales.
        """
        if not GOOGLE_CALENDAR_AVAILABLE:
            return False

        try:
            flow = Flow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=SCOPES,
                state=session['state'],
                redirect_uri=url_for('oauth2callback', _external=True)
            )

            flow.fetch_token(authorization_response=authorization_response)
            self.credentials = flow.credentials

            # Guardar credenciales
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(self.credentials, token)

            # Crear servicio
            self.service = build('calendar', 'v3', credentials=self.credentials)
            return True
        except Exception as e:
            print(f"Error en callback OAuth: {e}")
            return False

    def create_event(self, tarea: TareaCalendar) -> Optional[str]:
        """
        Crea un evento en Google Calendar a partir de una tarea.

        Returns:
            ID del evento creado o None si falla
        """
        if not self.service:
            print("Servicio de Google Calendar no inicializado")
            return None

        try:
            # Determinar color según prioridad
            color_id = {
                'alta': '11',  # Rojo
                'media': '5',  # Amarillo
                'baja': '2'    # Verde
            }.get(tarea.get_prioridad(), '1')

            # Crear fecha de inicio y fin (todo el día)
            fecha = tarea.get_fecha_entrega()

            event = {
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
                        {'method': 'email', 'minutes': 24 * 60},  # 1 día antes
                        {'method': 'popup', 'minutes': 60},       # 1 hora antes
                    ],
                },
                'colorId': color_id,
            }

            event = self.service.events().insert(calendarId='primary', body=event).execute()
            print(f'Evento creado: {event.get("htmlLink")}')
            return event.get('id')

        except HttpError as e:
            print(f"Error al crear evento: {e}")
            return None
        except Exception as e:
            print(f"Error inesperado: {e}")
            return None

    def update_event(self, event_id: str, tarea: TareaCalendar) -> bool:
        """
        Actualiza un evento existente en Google Calendar.
        """
        if not self.service:
            return False

        try:
            color_id = {
                'alta': '11',
                'media': '5',
                'baja': '2'
            }.get(tarea.get_prioridad(), '1')

            fecha = tarea.get_fecha_entrega()

            event = {
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
                'colorId': color_id,
            }

            self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            return True

        except Exception as e:
            print(f"Error al actualizar evento: {e}")
            return False

    def delete_event(self, event_id: str) -> bool:
        """
        Elimina un evento de Google Calendar.
        """
        if not self.service:
            return False

        try:
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            return True
        except Exception as e:
            print(f"Error al eliminar evento: {e}")
            return False

    def get_calendar_list(self) -> List[Dict]:
        """
        Obtiene la lista de calendarios disponibles.
        """
        if not self.service:
            return []

        try:
            calendars = self.service.calendarList().list().execute()
            return calendars.get('items', [])
        except Exception as e:
            print(f"Error al obtener calendarios: {e}")
            return []


# ============================================================================
# SISTEMA DE TAREAS WEB
# ============================================================================
class SistemaTareasWeb:
    """
    Sistema de tareas adaptado para la aplicación web.
    """

    ARCHIVO_TAREAS = 'tareas_web.json'

    def __init__(self):
        self.tareas: List[TareaCalendar] = []
        self.calendar_manager = GoogleCalendarManager()
        self.cargar_tareas()

    def cargar_tareas(self) -> None:
        """Carga las tareas desde el archivo JSON."""
        try:
            if os.path.exists(self.ARCHIVO_TAREAS):
                with open(self.ARCHIVO_TAREAS, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                    self.tareas = [TareaCalendar.from_dict(t) for t in datos]
        except Exception as e:
            print(f"Error al cargar tareas: {e}")
            self.tareas = []

    def guardar_tareas(self) -> None:
        """Guarda las tareas en el archivo JSON."""
        try:
            with open(self.ARCHIVO_TAREAS, 'w', encoding='utf-8') as f:
                json.dump([t.to_dict() for t in self.tareas], f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar tareas: {e}")

    def agregar_tarea(self, nombre: str, fecha: str, prioridad: str,
                      sync_calendar: bool = False) -> Dict:
        """
        Agrega una nueva tarea y opcionalmente la sincroniza con Google Calendar.
        """
        # Validaciones
        if not nombre or not nombre.strip():
            return {'success': False, 'error': 'El nombre es obligatorio'}

        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            return {'success': False, 'error': 'Fecha inválida. Use formato YYYY-MM-DD'}

        if prioridad.lower() not in ['alta', 'media', 'baja']:
            return {'success': False, 'error': 'Prioridad debe ser: alta, media o baja'}

        # Crear tarea
        tarea = TareaCalendar(nombre.strip(), fecha, prioridad.lower())

        # Sincronizar con Google Calendar si está habilitado
        event_id = None
        if sync_calendar and self.calendar_manager.load_credentials():
            event_id = self.calendar_manager.create_event(tarea)
            if event_id:
                tarea.set_google_event_id(event_id)

        self.tareas.append(tarea)
        self.guardar_tareas()

        return {
            'success': True,
            'tarea': tarea.to_dict(),
            'synced': event_id is not None
        }

    def obtener_tareas(self, filtro: str = 'todas') -> List[Dict]:
        """
        Obtiene las tareas, opcionalmente filtradas.
        """
        tareas_filtradas = self.tareas

        if filtro == 'pendientes':
            tareas_filtradas = [t for t in self.tareas if t.get_estado() == 'pendiente']
        elif filtro == 'completadas':
            tareas_filtradas = [t for t in self.tareas if t.get_estado() == 'completada']
        elif filtro == 'alta':
            tareas_filtradas = [t for t in self.tareas if t.get_prioridad() == 'alta']
        elif filtro == 'proximas':
            hoy = datetime.now().date()
            tareas_filtradas = [
                t for t in self.tareas
                if t.get_estado() == 'pendiente'
                and (datetime.strptime(t.get_fecha_entrega(), "%Y-%m-%d").date() - hoy).days <= 3
            ]

        return [t.to_dict() for t in tareas_filtradas]

    def completar_tarea(self, index: int, sync_calendar: bool = False) -> Dict:
        """Marca una tarea como completada."""
        try:
            if index < 0 or index >= len(self.tareas):
                return {'success': False, 'error': 'Tarea no encontrada'}

            tarea = self.tareas[index]
            tarea.set_estado('completada')

            # Actualizar en Google Calendar si tiene evento asociado
            if sync_calendar and tarea.get_google_event_id() and self.calendar_manager.load_credentials():
                # Podríamos actualizar el título para indicar que está completada
                pass

            self.guardar_tareas()
            return {'success': True, 'tarea': tarea.to_dict()}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def eliminar_tarea(self, index: int, sync_calendar: bool = False) -> Dict:
        """Elimina una tarea."""
        try:
            if index < 0 or index >= len(self.tareas):
                return {'success': False, 'error': 'Tarea no encontrada'}

            tarea = self.tareas[index]

            # Eliminar de Google Calendar si tiene evento asociado
            if sync_calendar and tarea.get_google_event_id() and self.calendar_manager.load_credentials():
                self.calendar_manager.delete_event(tarea.get_google_event_id())

            del self.tareas[index]
            self.guardar_tareas()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def obtener_estadisticas(self) -> Dict:
        """Obtiene estadísticas de las tareas."""
        total = len(self.tareas)
        if total == 0:
            return {
                'total': 0,
                'completadas': 0,
                'pendientes': 0,
                'productividad': 0,
                'por_prioridad': {'alta': 0, 'media': 0, 'baja': 0}
            }

        completadas = sum(1 for t in self.tareas if t.get_estado() == 'completada')
        pendientes = total - completadas
        productividad = (completadas / total) * 100

        prioridad_alta = sum(1 for t in self.tareas if t.get_prioridad() == 'alta')
        prioridad_media = sum(1 for t in self.tareas if t.get_prioridad() == 'media')
        prioridad_baja = sum(1 for t in self.tareas if t.get_prioridad() == 'baja')

        return {
            'total': total,
            'completadas': completadas,
            'pendientes': pendientes,
            'productividad': round(productividad, 1),
            'por_prioridad': {
                'alta': prioridad_alta,
                'media': prioridad_media,
                'baja': prioridad_baja
            }
        }

    def obtener_alertas(self) -> List[Dict]:
        """Obtiene las tareas con alertas de vencimiento."""
        hoy = datetime.now().date()
        alertas = []

        for tarea in self.tareas:
            if tarea.get_estado() == 'pendiente':
                fecha_entrega = datetime.strptime(tarea.get_fecha_entrega(), "%Y-%m-%d").date()
                dias_restantes = (fecha_entrega - hoy).days

                if dias_restantes <= 3:
                    alertas.append({
                        'tarea': tarea.to_dict(),
                        'dias_restantes': dias_restantes,
                        'tipo': 'vencida' if dias_restantes < 0 else 'urgente' if dias_restantes <= 1 else 'proxima'
                    })

        return alertas


# Instancia global del sistema
sistema = SistemaTareasWeb()

# ============================================================================
# RUTAS DE LA APLICACIÓN WEB
# ============================================================================

@app.route('/')
def index():
    """Página principal."""
    calendar_connected = sistema.calendar_manager.load_credentials()
    return render_template('index.html', calendar_connected=calendar_connected)


@app.route('/api/tareas', methods=['GET'])
def api_get_tareas():
    """API: Obtener todas las tareas."""
    filtro = request.args.get('filtro', 'todas')
    tareas = sistema.obtener_tareas(filtro)
    return jsonify({'success': True, 'tareas': tareas})


@app.route('/api/tareas', methods=['POST'])
def api_add_tarea():
    """API: Agregar nueva tarea."""
    data = request.get_json()

    nombre = data.get('nombre', '')
    fecha = data.get('fecha', '')
    prioridad = data.get('prioridad', 'media')
    sync_calendar = data.get('sync_calendar', False)

    resultado = sistema.agregar_tarea(nombre, fecha, prioridad, sync_calendar)
    return jsonify(resultado)


@app.route('/api/tareas/<int:index>/completar', methods=['POST'])
def api_completar_tarea(index):
    """API: Marcar tarea como completada."""
    data = request.get_json() or {}
    sync_calendar = data.get('sync_calendar', False)

    resultado = sistema.completar_tarea(index, sync_calendar)
    return jsonify(resultado)


@app.route('/api/tareas/<int:index>', methods=['DELETE'])
def api_eliminar_tarea(index):
    """API: Eliminar tarea."""
    data = request.get_json() or {}
    sync_calendar = data.get('sync_calendar', False)

    resultado = sistema.eliminar_tarea(index, sync_calendar)
    return jsonify(resultado)


@app.route('/api/estadisticas', methods=['GET'])
def api_get_estadisticas():
    """API: Obtener estadísticas."""
    stats = sistema.obtener_estadisticas()
    return jsonify({'success': True, 'estadisticas': stats})


@app.route('/api/alertas', methods=['GET'])
def api_get_alertas():
    """API: Obtener alertas."""
    alertas = sistema.obtener_alertas()
    return jsonify({'success': True, 'alertas': alertas})


# ============================================================================
# RUTAS PARA GOOGLE CALENDAR INTEGRATION
# ============================================================================

@app.route('/calendar/auth')
def calendar_auth():
    """Inicia el flujo de autorización de Google Calendar."""
    try:
        auth_url = sistema.calendar_manager.get_auth_url()
        return redirect(auth_url)
    except Exception as e:
        flash(f'Error al iniciar autenticación: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/calendar/oauth2callback')
def oauth2callback():
    """Callback de OAuth2 de Google."""
    try:
        authorization_response = request.url
        if sistema.calendar_manager.handle_callback(authorization_response):
            flash('✅ Cuenta de Google Calendar conectada exitosamente!', 'success')
        else:
            flash('❌ Error al conectar con Google Calendar', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('index'))


@app.route('/calendar/status')
def calendar_status():
    """Verifica el estado de la conexión con Google Calendar."""
    connected = sistema.calendar_manager.load_credentials()
    return jsonify({
        'connected': connected,
        'available': GOOGLE_CALENDAR_AVAILABLE
    })


@app.route('/calendar/disconnect')
def calendar_disconnect():
    """Desconecta la cuenta de Google Calendar."""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
    flash('Cuenta de Google Calendar desconectada', 'info')
    return redirect(url_for('index'))


# ============================================================================
# EJECUCIÓN
# ============================================================================

if __name__ == '__main__':
    # Crear directorios necesarios
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)

    print("🚀 Iniciando Sistema Académico de Tareas Web...")
    print("📱 Accede a: http://localhost:5000")
    print("")
    print("Para usar Google Calendar:")
    print("1. Ve a https://console.cloud.google.com/")
    print("2. Crea un proyecto y habilita Google Calendar API")
    print("3. Crea credenciales OAuth2 y descarga client_secrets.json")
    print("4. Coloca client_secrets.json en la carpeta del proyecto")
    print("")

    app.run(debug=True, host='0.0.0.0', port=5000)
