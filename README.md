# 📚 Sistema Académico de Administración de Tareas

Aplicación completa en Python para gestionar tareas académicas con integración a **Google Calendar**.

## ✨ Características Principales

- ✅ **CRUD Completo**: Agregar, ver, completar y eliminar tareas
- 💾 **Persistencia**: Almacenamiento automático en archivo JSON
- 📅 **Google Calendar**: Sincronización automática de tareas con tu calendario
- 🔔 **Alertas Inteligentes**: Notificaciones de tareas próximas a vencer
- 📊 **Estadísticas**: Métricas de productividad y conteo por prioridad
- 🔒 **Validaciones**: Manejo robusto de errores con try/except
- 🎨 **Interfaz Web**: Panel de control moderno y responsive
- 💻 **Google Colab**: Versión especial para Colab con autenticación integrada

---

## 🚀 Opciones de Uso

### Opción 1: Google Colab (Recomendado para principiantes)

#### Paso 1: Instalar dependencias
```python
!pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

#### Paso 2: Copiar y ejecutar el script
1. Abre [Google Colab](https://colab.research.google.com/)
2. Sube el archivo `sistema_academico_tareas_colab.py`
3. Ejecuta: `exec(open('sistema_academico_tareas_colab.py').read())`

#### Paso 3: Autenticar con Google
- La primera vez que sincronices con Calendar, se te pedirá autorización
- Sigue los pasos de autenticación en el navegador
- ¡Listo! Tus tareas se sincronizarán automáticamente

---

### Opción 2: Aplicación Web (Flask)

#### Requisitos previos
- Python 3.8+
- Cuenta de Google Cloud Platform (para Calendar API)

#### Instalación local
```bash
# Clonar repositorio
git clone https://github.com/Alejomango11/proyecto-final.git
cd proyecto-final

# Instalar dependencias
pip install -r requirements.txt

# Configurar Google Calendar API (ver instrucciones abajo)
# Copiar client_secrets.json al directorio del proyecto

# Ejecutar aplicación
python app.py
```

#### Configuración de Google Calendar API
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto (o usa uno existente)
3. Habilita la **Google Calendar API**:
   - APIs y servicios > Biblioteca
   - Buscar "Google Calendar API"
   - Click en "Habilitar"
4. Crea credenciales OAuth2:
   - APIs y servicios > Credenciales
   - Crear credenciales > ID de cliente OAuth
   - Tipo de aplicación: "Aplicación web"
   - Orígenes autorizados: `http://localhost:5000`
   - URIs de redirección: `http://localhost:5000/calendar/oauth2callback`
5. Descarga el archivo JSON y renómbralo a `client_secrets.json`
6. Colócalo en la raíz del proyecto

#### Uso de la aplicación web
```bash
python app.py
```
Abre tu navegador en: `http://localhost:5000`

---

### Opción 3: Versión Consola (Local)

```bash
python sistema_academico_tareas.py
```

---

## 📋 Menú de Opciones

| Opción | Descripción |
|--------|-------------|
| 1 | ➕ Agregar nueva tarea |
| 2 | 📋 Ver todas las tareas |
| 3 | ✔️ Marcar tarea como completada |
| 4 | 🗑️ Eliminar tarea |
| 5 | 📅 Ver tareas ordenadas por fecha |
| 6 | 🚨 Mostrar alertas de vencimiento |
| 7 | 📊 Ver estadísticas |
| 8 | 🔗 Conectar Google Calendar (Colab) |
| 9 | 🚪 Salir y guardar |

---

## 📝 Formato de Datos

- **Fecha de entrega**: `YYYY-MM-DD` (ejemplo: `2024-12-31`)
- **Prioridades**: `alta`, `media` o `baja`
- **Estados**: `pendiente` o `completada`

---

## 📅 Integración con Google Calendar

### ¿Qué se sincroniza?
- ✅ Eventos de todo el día en tu calendario principal
- ✅ Recordatorios automáticos (1 día antes por email, 1 hora antes popup)
- ✅ Códigos de color según prioridad:
  - 🔴 **Alta**: Rojo
  - 🟡 **Media**: Amarillo
  - 🟢 **Baja**: Verde

### ¿Cómo funciona?
1. Al agregar una tarea, marca la opción "Sincronizar con Google Calendar"
2. El evento se crea automáticamente en tu calendario
3. Al eliminar una tarea, el evento también se elimina
4. Puedes desconectar Google Calendar en cualquier momento

---

## 🔔 Alertas Automáticas

El sistema muestra alertas para:
- 🔴 **Tareas vencidas** que siguen pendientes
- 🟠 **Tareas que vencen hoy**
- 🟡 **Tareas que vencen en los próximos 3 días**

Las alertas se muestran:
- Al iniciar el programa
- En el panel de alertas (versión web)
- Al solicitarlas explícitamente (opción 6)

---

## 📊 Estadísticas

El sistema calcula automáticamente:
- **Total de tareas**
- **Tareas completadas**
- **Tareas pendientes**
- **Porcentaje de productividad** (completadas / total × 100)
- **Distribución por prioridad**

---

## 🔒 Validaciones Implementadas

- ✅ Formato de fecha `YYYY-MM-DD`
- ✅ Prioridad válida (`alta`, `media`, `baja`)
- ✅ Número de tarea existente
- ✅ Opción de menú numérica válida
- ✅ Todos los errores muestran mensajes claros sin cerrar el programa

---

## 📁 Estructura del Proyecto

```
proyecto-final/
├── app.py                              # Aplicación web Flask
├── sistema_academico_tareas.py         # Versión consola (local)
├── sistema_academico_tareas_colab.py   # Versión Google Colab
├── requirements.txt                    # Dependencias
├── client_secrets.json.example         # Ejemplo de configuración OAuth
├── tareas.json                         # Almacenamiento de tareas (local)
├── tareas_web.json                     # Almacenamiento de tareas (web)
├── README.md                           # Este archivo
├── templates/
│   └── index.html                      # Interfaz web
├── static/
│   ├── css/
│   │   └── style.css                   # Estilos CSS
│   └── js/
│       └── app.js                      # JavaScript frontend
```

---

## 🛠️ Estructura del Código

```
Clase Tarea
├── Constructor y atributos
├── Getters y Setters
├── Método __str__ para formateo
└── Métodos de serialización JSON

Clase GoogleCalendarSync (Colab) / GoogleCalendarManager (Web)
├── Autenticación OAuth2
├── Crear evento
├── Eliminar evento
└── Actualizar evento

Clase SistemaTareas
├── Persistencia (cargar/guardar JSON)
├── Validaciones (fecha, prioridad, índices)
├── Operaciones CRUD con sincronización
├── Consultas y estadísticas
└── Alertas de vencimiento
```

---

## 🗄️ Almacenamiento

Las tareas se guardan automáticamente en formato JSON:

```json
[
  {
    "nombre": "Entregar proyecto de Python",
    "fecha_entrega": "2024-06-15",
    "prioridad": "alta",
    "estado": "pendiente",
    "google_event_id": "abc123xyz"
  }
]
```

---

## 🎨 Capturas de Pantalla

### Versión Web
- **Dashboard**: Estadísticas en tiempo real
- **Lista de tareas**: Visualización con indicadores de prioridad
- **Formulario**: Agregar tareas con sincronización opcional
- **Alertas**: Panel de notificaciones de vencimiento

### Versión Colab
- Interfaz de consola interactiva
- Autenticación integrada con Google
- Mensajes claros con emojis

---

## ⚠️ Notas Importantes

### Seguridad
- El archivo `client_secrets.json` contiene credenciales sensibles
- **NUNCA** lo subas a GitHub (está en .gitignore)
- El token de autenticación se guarda en `token.pickle` (también en .gitignore)

### Límites de Google Calendar API
- Límite de 1,000,000 de consultas por día (cuota gratuita)
- Para uso personal, es más que suficiente

### Compatibilidad
- ✅ Google Colab
- ✅ Python 3.8+
- ✅ Navegadores modernos (Chrome, Firefox, Safari, Edge)
- ✅ Windows, macOS, Linux

---

## 🆘 Solución de Problemas

### Error: "Archivo client_secrets.json no encontrado"
**Solución**: Sigue las instrucciones de configuración de Google Calendar API arriba.

### Error: "Error de autenticación con Google"
**Solución**: 
1. Elimina el archivo `token.pickle`
2. Vuelve a intentar la autenticación
3. Asegúrate de habilitar Google Calendar API en tu proyecto

### Error: "No module named 'google'"
**Solución**: Instala las dependencias:
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Las tareas no se guardan en Colab
**Solución**: En Colab, descarga manualmente el archivo `tareas.json` antes de cerrar la sesión:
```python
from google.colab import files
files.download('/content/tareas.json')
```

---

## 📄 Licencia

Proyecto académico desarrollado con fines educativos.

---

## 👨‍💻 Autor

Desarrollado como proyecto final de programación en Python.

---

## 🙏 Agradecimientos

- Google Calendar API por la integración de calendario
- Flask por el framework web
- Font Awesome por los iconos

---

**¿Preguntas o problemas?** 
Abre un issue en el repositorio o revisa la documentación de [Google Calendar API](https://developers.google.com/calendar/api/guides/overview).
