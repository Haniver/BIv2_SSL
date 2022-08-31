import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import Tarjeta from '../componentes/auxiliares/Tarjeta'
import fechas_srv from '../services/fechas_srv'
import EjesMultiples from '../componentes/graficos/EjesMultiples'
import Tabla from '../componentes/tablas/Tabla'
import TablaExpandible from '../componentes/tablas/TablaExpandible'
import tarjetasCombinadas from '../services/tarjetasCombinadas'
import TarjetaEnFila from '../componentes/auxiliares/TarjetaEnFila'
import Barras from '../componentes/graficos/Barras'
// import userService from '../services/user.service'

import {
  DollarSign,
  Calendar,
  Target,
  Divide,
  DivideCircle,
  FastForward,
  Navigation2,
  PieChart
} from 'react-feather'

const CostoPorPedido = () => {

  const [region, setRegion] = useState('')
  const [zona, setZona] = useState('')
  const [tienda, setTienda] = useState('')
  const [metodoEnvio, setMetodoEnvio] = useState('')
  const [anio, setAnio] = useState(0)
  const [mes, setMes] = useState(0)

  // useEffect(() => {
  //   console.log(`anio: ${anio}`)
  //   console.log(`mes: ${mes}`)
  // }, [anio, mes])

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
          <TablaExpandible titulo='Tabla General' yLabel='Pesos'seccion={seccion} mes={mes} anio={anio} region={region} zona={zona} tienda={tienda} metodoEnvio={metodoEnvio} />
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
