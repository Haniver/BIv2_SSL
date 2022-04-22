import { useState, useEffect } from 'react'
import { Row, Col } from 'reactstrap'
import fechas_srv from '../services/fechas_srv'
import Tabla from '../componentes/tablas/Tabla'
import Filtro from '../componentes/auxiliares/Filtro'
import UpdateFaltantes from '../componentes/auxiliares/UpdateFaltantes'

const ReporteFaltantes = () => {
    const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: ''})
    const [depto, setDepto] = useState('')
    const [subDepto, setSubDepto] = useState('')
    const [region, setRegion] = useState('')
    const [zona, setZona] = useState('')
    const [tienda, setTienda] = useState('')
    const [producto, setProducto] = useState({nombre: '', sku: '', fecha: '', tienda: ''})
    const [reloadTabla, setReloadTabla] = useState(0)
    const [botonEnviar, setBotonEnviar] = useState(0)

    const seccion = 'ReporteFaltantes'

  return (
    <>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro botonEnviar={botonEnviar} setBotonEnviar={setBotonEnviar} fechas={fechas} region={region} zona={zona} tienda={tienda} depto={depto} subDepto={subDepto} setFechas={setFechas} setRegion={setRegion} setZona={setZona} setTienda={setTienda} setDepto={setDepto} setSubDepto={setSubDepto} />
        </Col>
        {botonEnviar > 0 && <Col sm='12' lg={(producto.nombre === '') ? 12 : 8}>
          <Tabla titulo='Reporte de Faltantes' botonEnviar={botonEnviar} fechas={fechas} region={region} zona={zona} tienda={tienda} depto={depto} subDepto={subDepto} seccion={seccion} reload={reloadTabla} setProducto={setProducto} />
        </Col>}
        {producto.nombre !== '' && <Col sm='12' lg='4'>
            <UpdateFaltantes producto={producto} setProducto={setProducto} reloadTabla={reloadTabla} setReloadTabla={setReloadTabla} fechas={fechas} tienda={tienda} />
        </Col>}
      </Row>
    </>
  )
}
export default ReporteFaltantes
