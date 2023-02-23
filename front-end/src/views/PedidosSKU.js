import { useState, useEffect } from 'react'
import { Row, Col } from 'reactstrap'
import fechas_srv from '../services/fechas_srv'
import Tabla from '../componentes/tablas/Tabla'
import Filtro from '../componentes/auxiliares/Filtro'
import userService from '../services/user.service'
// import userService from '../services/user.service'

const PedidosSKU = () => {
    const [fechas, setFechas] = useState({
        fecha_ini: fechas_srv.actualVencida(),
        fecha_fin: fechas_srv.actualVencida()
    })
    const [region, setRegion] = useState(userService.getRegionPorNivel())
    const [zona, setZona] = useState(userService.getZonaPorNivel())
    const [tienda, setTienda] = useState(userService.getTiendaPorNivel())
    const [sku, setSku] = useState('')
    const [botonEnviar, setBotonEnviar] = useState(0)

    const seccion = 'PedidosSKU'

    // useEffect(() => {
    //     console.log(`Fechas desde parent:`)
    //     console.log(fechas)
    // }, [fechas])

  return (
    <>
      {/* {userService.getNivel() <= 3 && <Row className='match-height'>
        <Col sm='12'>
          <h2 className='centrado'>{userService.getLugarNombre()}</h2>
        </Col>
      </Row>} */}
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro sku={sku} fechas={fechas} rango_max_dias={15} region={region} zona={zona} tienda={tienda} setSku={setSku} setFechas={setFechas} setRegion={setRegion} setZona={setZona} setTienda={setTienda} botonEnviar={botonEnviar} setBotonEnviar={setBotonEnviar} />
        </Col>
      </Row>
      <Row className='match-height'>
      {botonEnviar > 0 && <Col sm='12'>
          <Tabla titulo='Pedidos SKU' botonEnviar={botonEnviar} sku={sku} fechas={fechas} region={region} zona={zona} tienda={tienda} seccion={seccion} />
        </Col>}
      </Row>
    </>
  )
}
export default PedidosSKU
