import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import EjesMultiples from '../componentes/graficos/EjesMultiples'
import TablaCostos from '../componentes/tablas/TablaCostos'
// import userService from '../services/user.service'

const CostoPorPedido = () => {

  const [region, setRegion] = useState('')
  const [zona, setZona] = useState('')
  const [tienda, setTienda] = useState('')
  const [metodoEnvio, setMetodoEnvio] = useState('')
  const [anio, setAnio] = useState(0)
  const [mes, setMes] = useState(0)
  const [filtCostosEnvio, setFiltCostosEnvio] = useState(0)
  const [filtCostosRHxPedido, setFiltCostosRHxPedido] = useState(0)
  const [filtCostosTotalxPedido, setFiltCostosTotalxPedido] = useState(0)

  const seccion = 'CostoPorPedido'

  return (
    <>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro anioOpcional={anio} mesOpcional={mes} region={region} zona={zona} tienda={tienda} metodoEnvio={metodoEnvio} setAnioOpcional={setAnio} setMesOpcional={setMes} setRegion={setRegion} setZona={setZona} setTienda={setTienda} setMetodoEnvio={setMetodoEnvio} />
        </Col>
      </Row>
      {(metodoEnvio === '') && <Row className='match-height'>
        <Col sm='12'>
          <EjesMultiples titulo='Costo por Método de envío' seccion={seccion} formato='moneda' yLabel='Pesos' mes={mes} anio={anio} region={region} zona={zona} tienda={tienda} metodoEnvio={metodoEnvio} />
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col sm='12'>
          <TablaCostos titulo='Tabla General' yLabel='Pesos' seccion={seccion} mes={mes} anio={anio} region={region} zona={zona} tienda={tienda} metodoEnvio={metodoEnvio} />
        </Col>
      </Row>
      {/* <Row className='match-height'>
        <Col sm='12'>
          <EjesMultiples titulo='Pedidos por Picker: Top 20' formato='moneda' mes={mes} anio={anio} region={region} zona={zona} tienda={tienda} metodoEnvio={metodoEnvio} seccion={seccion} />
        </Col>
      </Row> */}
    </>
  )
}
export default CostoPorPedido
