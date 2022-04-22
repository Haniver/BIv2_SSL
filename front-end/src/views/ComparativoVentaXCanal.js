import { useState, useEffect } from 'react'
import { Row, Col } from 'reactstrap'
import fechas_srv from '../services/fechas_srv'
import Tabla from '../componentes/tablas/Tabla'
import Filtro from '../componentes/auxiliares/Filtro'
import UpdateFaltantes from '../componentes/auxiliares/UpdateFaltantes'

const ComparativoVentaXCanal = () => {
  const [region, setRegion] = useState('')
  const [zona, setZona] = useState('')
  const [tienda, setTienda] = useState('')
  const [botonEnviar, setBotonEnviar] = useState(0)

  const seccion = 'ComparativoVentaXCanal'

  return (
    <>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro botonEnviar={botonEnviar} setBotonEnviar={setBotonEnviar} region={region} zona={zona} tienda={tienda} setRegion={setRegion} setZona={setZona} setTienda={setTienda} />
        </Col>
        {botonEnviar > 0 && <Col sm='12'>
          <Tabla titulo='Comparativo Venta Por Canal' botonEnviar={botonEnviar} region={region} zona={zona} tienda={tienda} seccion={seccion} />
        </Col>}
      </Row>
    </>
  )
}
export default ComparativoVentaXCanal
