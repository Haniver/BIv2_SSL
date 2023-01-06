from fastapi import Depends, FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.routers import barras, columnasApiladas, columnasBasicas, columnasDrilldown, ejesMultiples, cargarFiltros, pie, tablas, tarjetas, login, tarjetasCombinadas, barrasApiladas, cargarMotivosFaltantes, ColumnasNps, spiderweb, columnasSuperpuestas, burbuja3d, areaBasica, distribucion3d, sankey, columnasAgrupadasYApiladas, markdown, ejesMultiplesApilados, tarjetasEnFila, tablasExpandibles, checarHash, leyendas
import app.servicios.urls as urls
from app.servicios.tareasDiarias import buscarExpirados, reducirArchivosLogs
from fastapi_utils.tasks import repeat_every

# app = FastAPI(dependencies=[Depends(get_query_token)])
app = FastAPI()

# Access-Control-Allow-Origin
origins = [
    urls.frontendUrlHttp(),
    urls.frontendUrlHttps(),
    urls.apiUrlHttp(),
    urls.apiUrlHttps(),
    urls.bdSQLHttp(),
    urls.bdSQLHttps(),
    urls.bdMongoHttp(),
    urls.bdMongoHttps()
]

app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"], # Allows all origins
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(barras.router)
app.include_router(columnasApiladas.router)
app.include_router(columnasBasicas.router)
app.include_router(columnasDrilldown.router)
app.include_router(ejesMultiples.router)
app.include_router(cargarFiltros.router)
app.include_router(login.router)
app.include_router(pie.router)
app.include_router(tablas.router)
app.include_router(tarjetas.router)
app.include_router(tarjetasCombinadas.router)
app.include_router(barrasApiladas.router)
app.include_router(cargarMotivosFaltantes.router)
app.include_router(ColumnasNps.router)
app.include_router(spiderweb.router)
app.include_router(columnasSuperpuestas.router)
app.include_router(burbuja3d.router)
app.include_router(areaBasica.router)
app.include_router(distribucion3d.router)
app.include_router(sankey.router)
app.include_router(columnasAgrupadasYApiladas.router)
app.include_router(markdown.router)
app.include_router(ejesMultiplesApilados.router)
app.include_router(tarjetasEnFila.router)
app.include_router(tablasExpandibles.router)
app.include_router(checarHash.router)
app.include_router(leyendas.router)

@app.get("/")
async def root():
    return {"message": "Nada por aquí."}

@app.on_event("startup")
@repeat_every(seconds=60 * 60 * 24)  # 1 día
# @repeat_every(seconds=30)  # 30 segundos (para debugging)
def remove_expired_tokens_task() -> None:
    buscarExpirados()
    reducirArchivosLogs()