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

const VentaSinImpuesto = () => {

  const [region, setRegion] = useState('')
  const [zona, setZona] = useState('')
  const [tienda, setTienda] = useState('')
  const [metodoEnvio, setMetodoEnvio] = useState('')
  const [anio, setAnio] = useState(0)
  const [mes, setMes] = useState(0)

  useEffect(() => {
    console.log(`anio: ${anio}`)
    console.log(`mes: ${mes}`)
  }, [anio, mes])

  const seccion = 'ConsolidadoCostos'

  return (
    <>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro anioOpcional={anio} mesOpcional={mes} region={region} zona={zona} tienda={tienda} metodoEnvio={metodoEnvio} setAnioOpcional={setAnio} setMesOpcional={setMes} setRegion={setRegion} setZona={setZona} setTienda={setTienda} setMetodoEnvio={setMetodoEnvio} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <TablaExpandible titulo='Tabla General' yLabel='Pesos'seccion={seccion} mes={mes} anio={anio} region={region} zona={zona} tienda={tienda} metodoEnvio={metodoEnvio} />
        </Col>
      </Row>
      {(metodoEnvio === '') && <Row className='match-height'>
        <Col sm='12'>
          <EjesMultiples titulo='Costo por Método de envío' seccion={seccion} formato='moneda' yLabel='Pesos' mes={mes} anio={anio} region={region} zona={zona} tienda={tienda} metodoEnvio={metodoEnvio} />
        </Col>
      </Row>}
      {/* {(tienda === false || tienda === '') && <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo={`Venta anual por mes: ${anio} vs. ${anio - 1} y Objetivo`} tituloAPI='Venta anual por mes: $anioActual vs. $anioAnterior y Objetivo' formato='moneda' yLabel='Pesos' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion} />
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col sm='12'>
          <EjesMultiples titulo={`Venta mensual por día: ${anio} vs. ${anio - 1} y Objetivo`} tituloAPI='Venta mensual por día: $anioActual vs. $anioAnterior y Objetivo' formato='moneda' yLabel='Pesos' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion} />
        </Col>
      </Row>
      {(tienda === false || tienda === '') && <Row className='match-height'>
        <Col sm='12'>
          <EjesMultiples titulo={`Venta anual por lugar: ${anio} vs. ${anio - 1} y Objetivo`} tituloAPI='Venta anual por lugar: $anioActual vs. $anioAnterior y Objetivo' formato='moneda' yLabel='Pesos' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion} />
        </Col>
      </Row>}
      {(tienda === false || tienda === '') && <Row className='match-height'>
        <Col sm='12'>
          <EjesMultiples titulo={`Venta mensual por lugar: ${anio} vs. ${anio - 1} y Objetivo`} tituloAPI='Venta mensual por lugar: $anioActual vs. $anioAnterior y Objetivo' formato='moneda' yLabel='Pesos' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion} />
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col sm='12'>
          <Tabla quitarBusqueda={true} titulo='Venta sin impuesto por Departamento o Sub Departamento' formato='moneda' yLabel='Pesos' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion} />
        </Col>
      </Row> */}
    </>
  )
}
export default VentaSinImpuesto
