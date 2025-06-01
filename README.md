# Aplicación de Registro de Asistencia con Streamlit y SQLite

Esta aplicación permite llevar un registro de asistencia semanal para estudiantes. Utiliza Streamlit para la interfaz de usuario y SQLite para el almacenamiento de datos.

## Características

* Registro de asistencia (Presente, Ausente, Tarde) para los días martes y jueves.
* Registro de causa de inasistencia y si está justificada.
* Navegación entre semanas.
* Visualización detallada de la asistencia semanal por estudiante.
* Los datos se guardan automáticamente en una base de datos SQLite local (`asistencia.db`).

## Configuración y Ejecución Local

1.  **Prerrequisitos:**
    * Python 3.7 o superior.
    * `pip` (manejador de paquetes de Python).

2.  **Descargar los archivos:**
    * `app.py`
    * `requirements.txt`
    * (Este `README.md`)

3.  **Crear un entorno virtual (recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

4.  **Instalar dependencias:**
    Coloca el archivo `requirements.txt` en el mismo directorio que `app.py` y ejecuta:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Ejecutar la aplicación:**
    Asegúrate de estar en el directorio donde guardaste `app.py`.
    ```bash
    streamlit run app.py
    ```
    La aplicación se abrirá automáticamente en tu navegador web. La base de datos `asistencia.db` se creará en el mismo directorio la primera vez que se ejecute la aplicación.

## Despliegue en Netlify (Consideraciones Importantes)

Netlify está diseñado principalmente para sitios estáticos y funciones serverless. Desplegar una aplicación Streamlit que depende de un archivo de base de datos SQLite **local y persistente** presenta desafíos:

* **Sistema de Archivos Efímero:** El sistema de archivos de Netlify donde se ejecuta tu aplicación es generalmente efímero. Esto significa que cualquier archivo `asistencia.db` creado o modificado por la aplicación **se perderá** cuando la instancia de la aplicación se detenga o reinicie (lo cual puede suceder frecuentemente). Cada nueva sesión podría empezar con una base de datos vacía.
* **Persistencia de Datos:** Para que los datos persistan entre sesiones o para múltiples usuarios en Netlify, necesitarías utilizar una solución de base de datos basada en la nube (ej. Firebase Firestore, Supabase, Neon, ElephantSQL para PostgreSQL, etc.) y modificar la aplicación para que se conecte a ella. Esto va en contra del requisito de usar SQLite para este ejemplo.

**Si aún deseas intentar desplegar en Netlify (con la limitación de que los datos de SQLite NO serán persistentes):**

1.  **Prepara tu repositorio Git:**
    * Asegúrate de que `app.py`, `requirements.txt` (y opcionalmente un archivo `runtime.txt` especificando la versión de Python si es necesario) estén en tu repositorio.
    * **No incluyas el archivo `asistencia.db` en el repositorio** si no quieres que se despliegue una versión específica de la base de datos (además, no se actualizaría de forma persistente).

2.  **Configuración en Netlify:**
    * **Build command (Comando de construcción):**
        ```
        pip install -r requirements.txt
        ```
    * **Publish directory (Directorio de publicación):** Netlify no necesita un directorio de publicación para Streamlit de la misma forma que para sitios estáticos. Puedes dejarlo como el directorio raíz o el que Netlify sugiera.
    * **Función de Netlify (si usas un enfoque avanzado) o Comando de Ejecución (si Netlify lo soporta directamente para Streamlit via `netlify.toml`):**
        La forma más común de desplegar Streamlit es ejecutar su servidor. Necesitarás configurar Netlify para que ejecute algo como:
        ```
        streamlit run app.py --server.port $PORT --server.enableCORS false --server.headless true
        ```
        Esto se puede especificar en un archivo `netlify.toml` en la raíz de tu proyecto:
        ```toml
        [build]
          command = "pip install -r requirements.txt"
          publish = "." # O el directorio que corresponda

        [[redirects]]
          from = "/*"
          to = "/.netlify/functions/streamlit_handler" # Si usas una función serverless
          status = 200

        # O si Netlify soporta directamente el comando de ejecución para el servidor:
        # [dev]
        #   command = "streamlit run app.py" # Para desarrollo local con Netlify CLI
        # Para el despliegue, la configuración del servidor de Streamlit es clave.
        # Netlify puede requerir que envuelvas la app Streamlit en una función serverless
        # si no hay soporte directo para ejecutar el servidor de Streamlit.

        # Una forma más directa si Netlify lo permite (puede variar):
        # [build]
        #   command = "pip install -r requirements.txt && streamlit run app.py --server.port $PORT --server.enableCORS false --server.headless true"
        #   publish = "." # No hay un "directorio de publicación" estático para Streamlit
        ```
        **Nota:** Desplegar aplicaciones con estado como Streamlit (que ejecutan un servidor Python persistente) en plataformas como Netlify puede ser complejo y a menudo requiere el uso de "Netlify Functions" para actuar como un proxy o ejecutar el proceso de Python, o usar contenedores si Netlify ofrece ese servicio (como Netlify Background Functions o similar).

**Recomendación:**
Para una aplicación Streamlit con persistencia de datos SQLite, es más adecuado desplegarla en un entorno donde tengas control sobre un sistema de archivos persistente, como:
* Un VPS (Servidor Privado Virtual).
* Plataformas PaaS que soporten aplicaciones Python con almacenamiento persistente (ej. Heroku con ciertos planes, Google Cloud Run con volúmenes, etc.).
* Ejecutarla localmente o en una red interna.

Si la persistencia de datos en el despliegue es crucial, considera cambiar SQLite por una base de datos en la nube.
