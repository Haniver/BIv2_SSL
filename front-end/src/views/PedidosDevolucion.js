import { useState, useEffect } from 'react'
import { Row, Col } from 'reactstrap'
import fechas_srv from '../services/fechas_srv'
import Tabla from '../componentes/tablas/Tabla'
import Filtro from '../componentes/auxiliares/Filtro'
import userService from '../services/user.service'

const PedidosDevolucion = () => {
    const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
    const [region, setRegion] = useState('')
    const [zona, setZona] = useState('')
    const [tienda, setTienda] = useState('')
    const [formato, setFormato] = useState('')
    const [botonEnviar, setBotonEnviar] = useState(0)

    const seccion = 'PedidosDevolucion'

  return (
    <>
      {userService.getNivel() <= 3 && <Row className='match-height'>
        <Col sm='12'>
          <h2 className='centrado'>{userService.getLugarNombre()}</h2>
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro botonEnviar={botonEnviar} setBotonEnviar={setBotonEnviar} fechas={fechas} region={region} zona={zona} tienda={tienda} formato={formato} setFechas={setFechas} setRegion={setRegion} setZona={setZona} setTienda={setTienda} setFormato={setFormato} />
        </Col>
      </Row>
      <Row className='match-height'>
      {botonEnviar > 0 && <Col sm='12'>
        <Tabla titulo='Pedidos Devolución' fechas={fechas} region={region} zona={zona} tienda={tienda} formato={formato} seccion={seccion} botonEnviar={botonEnviar} />
        </Col>}
      </Row>
    </>
  )
}
export default PedidosDevolucion
