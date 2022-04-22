import { useState, useEffect } from 'react'
import { Row, Col } from 'reactstrap'
import fechas_srv from '../services/fechas_srv'
import Tabla from '../componentes/tablas/Tabla'
import Filtro from '../componentes/auxiliares/Filtro'

const NPSDetalle = () => {
    const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
    const [region, setRegion] = useState('')
    const [zona, setZona] = useState('')
    const [tienda, setTienda] = useState('')
    const [botonEnviar, setBotonEnviar] = useState(0)

    const seccion = 'NPSDetalle'

  return (
    <>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro botonEnviar={botonEnviar} setBotonEnviar={setBotonEnviar} fechas={fechas} region={region} zona={zona} tienda={tienda} setFechas={setFechas} setRegion={setRegion} setZona={setZona} setTienda={setTienda} />
        </Col>
      </Row>
      <Row className='match-height'>
      {botonEnviar > 0 && <Col sm='12'>
          <Tabla titulo='Pedido Diario' fechas={fechas} region={region} zona={zona} tienda={tienda} seccion={seccion} botonEnviar={botonEnviar} />
        </Col>}
      </Row>
    </>
  )
}
export default NPSDetalle
