# 📚 Sistema Académico de Administración de Tareas

Aplicación completa en Python para gestionar tareas académicas con integración a **Google Calendar**. Diseñada específicamente para funcionar en **Google Colab**.

---

## ✨ Características

- ✅ **CRUD Completo**: Crear, leer, actualizar y eliminar tareas
- 💾 **Persistencia**: Guardado automático en archivo JSON
- 📅 **Google Calendar**: Sincronización automática de tareas con tu calendario
- 🔔 **Alertas**: Notificaciones de tareas vencidas y próximas a vencer
- 📊 **Estadísticas**: Métricas de productividad con gráficos de barras
- 🔍 **Búsqueda y Filtros**: Filtrar por estado, prioridad o buscar por nombre
- 🎨 **Interfaz Amigable**: Colores, emojis y diseño limpio en consola
- 🔒 **Validaciones**: Manejo robusto de errores sin cerrar el programa

---

## 🚀 Cómo usar en Google Colab

### Paso 1: Abrir Google Colab
1. Ve a [Google Colab](https://colab.research.google.com/)
2. Crea un **nuevo notebook**

### Paso 2: Instalar dependencias
En una celda, ejecuta:
```python
!pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Paso 3: Subir el archivo
1. Haz clic en el icono 📁 (Archivos) en el panel lateral izquierdo
2. Sube el archivo `sistema_academico_tareas4.py`

### Paso 4: Ejecutar
En una nueva celda, ejecuta:
```python
exec(open('sistema_academico_tareas4.py').read())
```

---

## 📋 Menú de Opciones

| Opción | Descripción |
|--------|-------------|
| **1** | ➕ Agregar nueva tarea |
| **2** | 📋 Ver tareas (con submenú de filtros) |
| **3** | ✔️ Marcar tarea como completada |
| **4** | 🗑️ Eliminar tarea |
| **5** | 📅 Ordenar tareas por fecha de entrega |
| **6** | 🚨 Mostrar alertas de vencimiento |
| **7** | 📊 Ver estadísticas de productividad |
| **8** | 📅 Sincronizar con Google Calendar |
| **9** | 🚪 Salir y guardar |

---

## 📅 Integración con Google Calendar

### 🔧 Configuración Requerida (IMPORTANTE)

Para usar la sincronización con Google Calendar, debes habilitar la API en tu cuenta de Google:

#### Paso 1: Habilitar Google Calendar API
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto (o selecciona uno existente)
3. Ve a **"APIs y servicios" → "Biblioteca"**
4. Busca **"Google Calendar API"** y haz clic en **"Habilitar"**

#### Paso 2: Configurar Pantalla de Consentimiento OAuth
1. Ve a **"APIs y servicios" → "Pantalla de consentimiento OAuth"**
2. Selecciona **"Externo"** (o Interno si tienes Google Workspace)
3. Completa la información requerida:
   - Nombre de la app: "Sistema Académico de Tareas"
   - Correo de soporte: tu correo
   - Dominio: (dejar vacío para uso personal)
   - Información de contacto del desarrollador: tu correo
4. Guarda y continúa

#### Paso 3: Agregar Alcances (Scopes)
1. En la pantalla de consentimiento, ve a la pestaña **"Alcances"** (Scopes)
2. Haz clic en **"Agregar o quitar alcances"**
3. Busca y selecciona:
   - `../auth/calendar` - "Ver y editar eventos en tu calendario"
4. Guarda los cambios

#### Paso 4: Agregar Usuario de Prueba
1. Ve a la pestaña **"Usuarios de prueba"**
2. Haz clic en **"Agregar usuarios"**
3. Ingresa tu correo de Gmail
4. Guarda los cambios

### 🚀 Uso en la Aplicación

Una vez configurado:

1. En el sistema, selecciona la **opción 8** del menú
2. Elige **"Autenticar con Google"**
3. Se abrirá un enlace de autorización
4. Inicia sesión con tu cuenta de Google (debe ser la que agregaste como usuario de prueba)
5. **IMPORTANTE**: Asegúrate de conceder los permisos para **"Ver y editar eventos"** en tu calendario
6. Copia el código de autorización y pégalo en Colab
7. ¡Listo! Ahora puedes sincronizar tareas

### ⚠️ Solución de Errores Comunes

#### Error: "Request had insufficient authentication scopes"
**Solución**: La autenticación no incluyó los permisos de Calendar. Debes:
1. Ir a [Configuración de cuenta Google](https://myaccount.google.com/permissions)
2. Buscar "Google Colab" o "Python" y revocar el acceso
3. Volver a autenticar en el sistema (opción 8)
4. Asegurarte de marcar la casilla de permisos de Calendar

#### Error: "Google Calendar API has not been used in project"
**Solución**: Ve a Google Cloud Console y habilita Google Calendar API (ver Paso 1 arriba)

### ¿Qué se sincroniza?
- ✅ Eventos de **todo el día** en tu calendario principal
- ✅ **Recordatorios automáticos**:
  - Email: 1 día antes
  - Notificación popup: 1 hora antes
- ✅ **Códigos de color** según prioridad:
  - 🔴 **Alta**: Rojo
  - 🟡 **Media**: Amarillo
  - 🟢 **Baja**: Verde

### Cómo sincronizar
- **Al agregar tarea**: Responde "s" cuando pregunte "¿Sincronizar con Google Calendar?"
- **Tareas existentes**: Opción 8 → "Sincronizar todas las tareas pendientes"

---

## 🔔 Alertas Automáticas

El sistema muestra alertas para:
- 🔴 **Tareas vencidas** que siguen pendientes
- 🔴 **Tareas que vencen hoy**
- 🟠 **Tareas que vencen mañana**
- 🟡 **Tareas que vencen en los próximos 3 días**

Las alertas se muestran:
- **Al iniciar** el programa
- **Al solicitarlas** (opción 6)

---

## 📊 Estadísticas

El sistema calcula automáticamente:
- **Total de tareas**
- **Tareas completadas** ✅
- **Tareas pendientes** ⏳
- **Porcentaje de productividad** (completadas / total × 100)
- **Distribución por prioridad** (alta/media/baja)

**Visualización**: Barra de progreso con colores según productividad:
- 🟢 ≥ 70%: Excelente
- 🟡 40-69%: Regular
- 🔴 < 40%: Necesita mejorar

---

## 🔍 Filtros y Búsqueda

Desde la **opción 2**, puedes:
- Ver **todas** las tareas
- Filtrar por **pendientes** o **completadas**
- Filtrar por **prioridad** (alta/media/baja)
- **Buscar** por nombre (búsqueda parcial, sin distinguir mayúsculas)

---

## 📝 Formato de Datos

### Fecha
- Formato: `YYYY-MM-DD`
- Ejemplo: `2024-12-31`

### Prioridad
- Opciones: `alta`, `media`, `baja`
- Se muestran con colores:
  - 🔴 Alta
  - 🟡 Media
  - 🟢 Baja

### Estado
- `pendiente` ⏳
- `completada` ✅

---

## 🛠️ Estructura del Código

```
sistema_academico_tareas.py
│
├── Clase Colores
│   └── Manejo de colores ANSI para consola
│
├── Clase Tarea
│   ├── Atributos: nombre, fecha, prioridad, estado, google_event_id
│   ├── Getters y Setters
│   ├── __str__ (representación en string)
│   ├── to_dict (serialización JSON)
│   └── from_dict (deserialización)
│
├── Clase GoogleCalendarSync
│   ├── autenticar()
│   ├── crear_evento()
│   └── eliminar_evento()
│
├── Clase SistemaAcademico
│   ├── Persistencia (cargar/guardar JSON)
│   ├── Validaciones (fecha, prioridad, índices)
│   ├── CRUD (agregar, ver, completar, eliminar)
│   ├── Búsqueda y filtros
│   ├── Ordenamiento por fecha
│   ├── Alertas de vencimiento
│   ├── Estadísticas
│   └── Sincronización con Calendar
│
└── Funciones de Interfaz
    ├── mostrar_banner()
    ├── mostrar_menu()
    ├── submenu_filtros()
    └── main()
```

---

## 💾 Persistencia

Las tareas se guardan automáticamente en:
- **Google Colab**: `/content/tareas.json`
- **Local**: `tareas.json` en el mismo directorio

**IMPORTANTE para Colab**:
- Los archivos en `/content/` se borran al cerrar la sesión
- Para conservar tus tareas, descarga el archivo antes de cerrar:
  ```python
  from google.colab import files
  files.download('/content/tareas.json')
  ```
- En tu próxima sesión, sube el archivo antes de ejecutar el programa

---

## 📄 Ejemplo de Uso

```
📚 SISTEMA ACADÉMICO DE TAREAS
              con Google Calendar Sync

✓ Se cargaron 3 tarea(s)

⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️
   🔔 NOTIFICACIONES:
   🔴 1 tarea(s) VENCIDA(S)!
   🟡 2 tarea(s) próximas a vencer
⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

============================================================
📋 MENÚ PRINCIPAL
============================================================

   [1] ➕  Agregar nueva tarea
   [2] 📋 Ver todas las tareas
   [3] ✔️   Marcar tarea como completada
   [4] 🗑️   Eliminar tarea
   [5] 📅 Ordenar tareas por fecha
   [6] 🚨 Mostrar alertas de vencimiento
   [7] 📊 Ver estadísticas
   [8] 📅 Sincronizar con Google Calendar
   [9] 🚪 Salir y guardar

============================================================

👉 Seleccione una opción (1-9):
```

---

## 🔒 Validaciones

El sistema valida mediante excepciones:

| Validación | Comportamiento |
|------------|----------------|
| Fecha vacía o incorrecta | Mensaje: "La fecha debe tener el formato YYYY-MM-DD" |
| Prioridad inválida | Mensaje: 'La prioridad debe ser "alta", "media" o "baja"' |
| Número de tarea inexistente | Mensaje: "La tarea #X no existe" |
| Opción de menú inválida | Mensaje: "Opción inválida. Usa 1-9." |
| Entrada no numérica donde se espera número | Mensaje: "Debes ingresar un número válido" |

**Todas las validaciones**:
- Muestran mensajes claros
- **NO cierran el programa**
- Permiten reintentar

---

## ⚙️ Requisitos Técnicos

### Dependencias
```
google-auth
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
```

### Python
- Versión 3.7 o superior
- Compatible con Google Colab

---

## 🆘 Solución de Problemas

### "ModuleNotFoundError: No module named 'google'"
**Solución**: Instala las dependencias:
```python
!pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### "Error de autenticación con Google"
**Solución**:
1. Asegúrate de tener conexión a internet
2. Intenta autenticar de nuevo (opción 8)
3. Si persiste, reinicia el runtime de Colab: **Runtime → Restart runtime**

### Las tareas no se guardan entre sesiones
**Solución**: Recuerda descargar `tareas.json` antes de cerrar Colab:
```python
from google.colab import files
files.download('/content/tareas.json')
```

### Error al sincronizar con Calendar
**Solución**:
1. Verifica que estés autenticado (opción 8 → opción 1)
2. Asegúrate de habilitar Google Calendar API en tu cuenta Google
3. Intenta sincronizar tareas individuales al agregarlas

---

## 🎨 Características Visuales

- **Colores ANSI** para mejor legibilidad
- **Emojis** para identificar rápidamente estados y prioridades
- **Banners y separadores** visuales
- **Barras de progreso** en estadísticas
- **Tablas alineadas** en el menú

---

## 📝 Licencia

Proyecto académico desarrollado con fines educativos.

---

## 👨‍💻 Autor

Desarrollado como proyecto final de programación en Python.

---

**¡Gracias por usar el Sistema Académico de Tareas! 📚✨**
