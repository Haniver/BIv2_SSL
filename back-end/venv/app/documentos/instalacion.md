# Manual para instalar el BI en un servidor nuevo

## Front end
* Copias la carpeta del front end sin node_modules del servidor origen al destino
* Checas qué versión de NodeJS tienes en el servidor origen:
``` console
    node --version
```
* En el nuevo servidor, instalas la versión de NodeJS que tienes en el origen
* Instalas dependencias con
``` console
    yarn
```
* Cambias url de la API en *src/services/customUrls.js*

## Back end:
* En el servidor origen, desde el folder app, creas un freeze de tu back end:
``` console
    python -m pip freeze > requirements.txt
```
* Copias el back end sin virtual environment; solo el folder app ~~ y requirements.txt
* En el destino, creas un entorno virtual nuevo
``` console
    python -m venv venv
```
* Le pones tu app folder ~~ y tu requirements.txt
* Desde el app folder, instalas requerimientos:
``` console
    pip install -r requirements.txt
```
* Corres Uvicorn:
``` console
    python -m uvicorn --reload --host 0.0.0.0 --port 8000 main:app
```
* Editas servicios/urls.py para que tenga la IP de tu nuevo servidor
* Instala el driver ODBC para SQL server en el servidor destino
* Si en *servicios/conectar_sql.py* tienes una versión del driver diferente a la que instalaste, cambia la línea de código
* Si te sale que la conexión no es confiable, agrega la bandera **IntegratedSecurity=true**