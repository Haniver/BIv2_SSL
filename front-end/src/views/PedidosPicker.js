import { useState, useEffect } from 'react'
import { Row, Col } from 'reactstrap'
import fechas_srv from '../services/fechas_srv'
import Tabla from '../componentes/tablas/Tabla'
import Filtro from '../componentes/auxiliares/Filtro'

const PedidosPicker = () => {
    const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
    const [region, setRegion] = useState('')
    const [zona, setZona] = useState('')
    const [tienda, setTienda] = useState('')
    const [botonEnviar, setBotonEnviar] = useState(0)
    const [agente, setAgente] =  useState('')

    const seccion = 'PedidosPicker'

    useEffect(() => {
      setAgente('')
    }, [botonEnviar])

  return (
    <>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro botonEnviar={botonEnviar} setBotonEnviar={setBotonEnviar} fechas={fechas} region={region} zona={zona} tienda={tienda} setFechas={setFechas}  setRegion={setRegion} setZona={setZona} setTienda={setTienda} />
        </Col>
      </Row>
      <Row className='match-height'>
      {botonEnviar > 0 && <Col sm='12'>
          <Tabla titulo='Pedido Diario' fechas={fechas} region={region} zona={zona} tienda={tienda} seccion={seccion} botonEnviar={botonEnviar} />
        </Col>}
      </Row>
      <Row className='match-height'>
      {/* WAWA te quedaste en ver por qué no se ve esta tabla */}
      {botonEnviar > 0 && tienda !== undefined && tienda !== '' && <Col sm='12'>
          <Tabla titulo='Pedidos Picker por Agente' fechas={fechas} region={region} zona={zona} tienda={tienda} seccion={seccion} setCambiarLugar={setAgente} botonEnviar={botonEnviar} />
        </Col>}
      </Row>
      <Row className='match-height'>
      {botonEnviar > 0 && agente !== undefined && agente !== '' && <Col sm='12'>
          <Tabla titulo={`Pedidos por Día para ${agente}`} tituloAPI='Pedidos por Día para $agente' fechas={fechas} region={region} zona={zona} tienda={tienda} fromSibling={agente} seccion={seccion} botonEnviar={botonEnviar} />
        </Col>}
      </Row>
    </>
  )
}
export default PedidosPicker
