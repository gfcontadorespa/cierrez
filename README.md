# AI Worker - Validador Cierre Z

Este repositorio contiene el worker inteligente para procesar imágenes de Cierres Z usando AI Vision (GPT-4o-mini).

## Componentes
- `background_worker.py`: El loop principal que monitorea la base de datos.
- `ai_vision_agent.py`: Agente de visión artificial para extraer datos.
- `db_manager.py`: Gestor de conexión a Postgres.

## Despliegue en Easypanel
1. Crear una nueva App desde este repositorio.
2. Configurar las variables de entorno (`.env`).
3. Montar el archivo `client_secret.json` y `authorized_user.json` o configurar sus contenidos como variables de entorno.
