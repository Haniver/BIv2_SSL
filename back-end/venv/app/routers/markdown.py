from fastapi import APIRouter, Depends
from app.auth import get_current_active_user
from app.servicios.permisos import permisoMarkdown
from fastapi.responses import FileResponse
from os import path

router = APIRouter(
    prefix="/markdown",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

@router.get("/{nombre_archivo}")
async def barras_apiladas (nombre_archivo: str, user: dict = Depends(get_current_active_user)):
    ruta = path.abspath(path.join(path.dirname(path.realpath(__file__))))
    if permisoMarkdown(user.id_rol, nombre_archivo):
        return FileResponse(f"{ruta}/../documentos/{nombre_archivo}.md")
    else:
        return FileResponse(f"{ruta}/../documentos/404.md")
    