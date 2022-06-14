import { useState, useEffect } from 'react'
import { Row, Col } from 'reactstrap'
import fechas_srv from '../services/fechas_srv'
import Tabla from '../componentes/tablas/Tabla'
import Filtro from '../componentes/auxiliares/Filtro'
// import userService from '../services/user.service'

const PedidoDiario = () => {
    const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
    const [region, setRegion] = useState('')
    const [zona, setZona] = useState('')
    const [tienda, setTienda] = useState('')
    const [estatus, setEstatus] = useState('')
    const [tipoEntrega3, setTipoEntrega3] = useState('')
    const [botonEnviar, setBotonEnviar] = useState(0)

    const seccion = 'PedidoDiario'

  return (
    <>
      {/* {userService.getNivel() <= 3 && <Row className='match-height'>
        <Col sm='12'>
          <h2 className='centrado'>{userService.getLugarNombre()}</h2>
        </Col>
      </Row>} */}
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro botonEnviar={botonEnviar} setBotonEnviar={setBotonEnviar} fechas={fechas} estatus={estatus} region={region} zona={zona} tienda={tienda} tipoEntrega3={tipoEntrega3} setFechas={setFechas} setEstatus={setEstatus} setRegion={setRegion} setZona={setZona} setTienda={setTienda} setTipoEntrega3={setTipoEntrega3} />
        </Col>
      </Row>
      <Row className='match-height'>
      {botonEnviar > 0 && <Col sm='12'>
        <Tabla titulo='Pedido Diario' fechas={fechas} estatus={estatus} region={region} zona={zona} tienda={tienda} tipoEntrega3={tipoEntrega3} seccion={seccion} botonEnviar={botonEnviar} />
        </Col>}
      </Row>
    </>
  )
}
export default PedidoDiario
