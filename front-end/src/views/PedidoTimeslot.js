import { useState, useEffect } from 'react'
import { Row, Col } from 'reactstrap'
import fechas_srv from '../services/fechas_srv'
import Tabla from '../componentes/tablas/Tabla'
import Filtro from '../componentes/auxiliares/Filtro'
import userService from '../services/user.service'
// import userService from '../services/user.service'

const PedidoTimeslot = () => {
    const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
    const [region, setRegion] = useState(userService.getRegionPorNivel())
    const [zona, setZona] = useState(userService.getZonaPorNivel())
    const [tienda, setTienda] = useState(userService.getTiendaPorNivel())
    const [detalle, setDetalle] = useState('dia')
    const [tipoEntrega2, setTipoEntrega2] = useState('premium-gross')
    const [botonEnviar, setBotonEnviar] = useState(0)

    const seccion = 'PedidoTimeslot'

    return (
    <>
      {/* {userService.getNivel() <= 3 && <Row className='match-height'>
        <Col sm='12'>
          <h2 className='centrado'>{userService.getLugarNombre()}</h2>
        </Col>
      </Row>} */}
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro botonEnviar={botonEnviar} setBotonEnviar={setBotonEnviar} fechas={fechas} detalle={detalle} region={region} zona={zona} tienda={tienda} tipoEntrega2={tipoEntrega2} setFechas={setFechas} setDetalle={setDetalle} setRegion={setRegion} setZona={setZona} setTienda={setTienda} setTipoEntrega2={setTipoEntrega2} />
        </Col>
      </Row>
      <Row className='match-height'>
      {botonEnviar > 0 && <Col sm='12'>
          <Tabla titulo='Ocupación de Timeslot' botonEnviar={botonEnviar} fechas={fechas} detalle={detalle} region={region} zona={zona} tienda={tienda} tipoEntrega2={tipoEntrega2} seccion={seccion} />
        </Col>}
      </Row>
    </>
  )
}
export default PedidoTimeslot
