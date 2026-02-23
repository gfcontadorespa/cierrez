# AI Worker - Validador Cierre Z

Este repositorio contiene el worker inteligente para procesar imágenes de Cierres Z usando AI Vision (GPT-4o-mini).

## Componentes
- `background_worker.py`: El loop principal que monitorea la base de datos.
- `ai_vision_agent.py`: Agente de visión artificial para extraer datos.
- `db_manager.py`: Gestor de conexión a Postgres.

## Despliegue en Easypanel
1. Crear una nueva App desde este repositorio.
2. Configurar las variables de entorno en la pestaña **Environment**:
   - `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_HOST`, `DB_PORT`
   - `APPSHEET_APP_ID`, `APPSHEET_ACCESS_KEY`
   - `OPENAI_API_KEY`
   - `GOOGLE_DRIVE_FOLDER_ID`
   - `GOOGLE_CREDENTIALS_JSON`: Pega aquí el contenido completo de tu archivo `authorized_user.json`.
3. ¡Desplegar! El worker se encargará del resto.
