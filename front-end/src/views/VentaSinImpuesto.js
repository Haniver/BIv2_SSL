import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import Tarjeta from '../componentes/auxiliares/Tarjeta'
import fechas_srv from '../services/fechas_srv'
import EjesMultiples from '../componentes/graficos/EjesMultiples'
import Tabla from '../componentes/tablas/Tabla'
import TarjetaEnFila from '../componentes/auxiliares/TarjetaEnFila'
import IndicadoresEnBarras from '../componentes/auxiliares/IndicadoresEnBarras'
import Leyenda from '../componentes/auxiliares/Leyenda'
import userService from '../services/user.service'
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

  const [region, setRegion] = useState(userService.getRegionPorNivel())
  const [zona, setZona] = useState(userService.getZonaPorNivel())
  const [tienda, setTienda] = useState(userService.getTiendaPorNivel())
  const [canal, setCanal] = useState(1)
  const [depto, setDepto] = useState('')
  const [subDepto, setSubDepto] = useState('')
  const [anio, setAnio] = useState(fechas_srv.anioActual())
  const [mes, setMes] = useState(fechas_srv.mesActual())
  const [dia, setDia] = useState(fechas_srv.diaActual())
  const [tarjetasCombinadasMes, setTarjetasCombinadasMes] = useState('cargando')
  const [tarjetasCombinadasAnio, setTarjetasCombinadasAnio] = useState('cargando')
  const [tarjetasCombinadasMesAlDia, setTarjetasCombinadasMesAlDia] = useState('cargando')
  const [botonEnviar, setBotonEnviar] = useState(0)

  // console.log(`fechas_srv.ultimoDiaVencidoDelMesReal(anio, mes): ${fechas_srv.ultimoDiaVencidoDelMesReal(anio, mes)}`)

  const seccion = 'VentaSinImpuesto'

  const [esMitad, setEsMitad] = useState(6)

  useEffect(() => {
    if (tienda === false || tienda === '') {
      setEsMitad(6)
    } else {
      setEsMitad(12)
    }
  }, [tienda])

  return (
    <>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro anio={anio} mes={mes} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} setAnio={setAnio} setMes={setMes} setRegion={setRegion} setZona={setZona} setTienda={setTienda} setCanal={setCanal} setDepto={setDepto} setSubDepto={setSubDepto} botonEnviar={botonEnviar} setBotonEnviar={setBotonEnviar} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <Leyenda seccion={seccion} titulo='Última actualización:' />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <IndicadoresEnBarras seccion={seccion} formato='moneda' titulo='Indicadores de Venta' cols={{ xl: '4', sm: '6' }} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} anio={anio} mes={mes} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg={esMitad}>
          <EjesMultiples titulo={`Venta anual por mes: ${anio} vs. ${anio - 1} y Objetivo`} tituloAPI='Venta anual por mes: $anioActual vs. $anioAnterior y Objetivo' formato='moneda' yLabel='Pesos' region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} seccion={seccion} anio={anio} mes={mes} />
        </Col>
      {(tienda === false || tienda === '') && 
        <Col sm='12' lg={esMitad}>
          <Tabla titulo={`Venta anual por mes: ${anio} vs. ${anio - 1} y Objetivo`} tituloAPI='Venta anual por mes: $anioActual vs. $anioAnterior y Objetivo' formato='moneda' yLabel='Pesos' region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion}  anio={anio}/>
        </Col>}
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <EjesMultiples titulo={`Venta mensual por día: ${anio} vs. ${anio - 1} (fecha comparable) y Objetivo`} tituloAPI='Venta mensual por día: $anioActual vs. $anioAnterior (fecha comparable) y Objetivo' formato='moneda' yLabel='Pesos' region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion} quitarCategoriaDeTooltip  anio={anio} />
        </Col>
      </Row>
      {(tienda === false || tienda === '') && <Row className='match-height'>
        <Col sm='12' lg='6'>
          <EjesMultiples titulo={`Venta anual por lugar: ${anio} vs. ${anio - 1} y Objetivo`} tituloAPI='Venta anual por lugar: $anioActual vs. $anioAnterior y Objetivo' formato='moneda' yLabel='Pesos' region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion}  anio={anio} />
        </Col>
        <Col sm='12' lg='6'>
          <EjesMultiples titulo={`Venta mensual por lugar: ${anio} vs. ${anio - 1} y Objetivo`} tituloAPI='Venta mensual por lugar: $anioActual vs. $anioAnterior y Objetivo' formato='moneda' yLabel='Pesos' region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion}  anio={anio} />
        </Col>
      </Row>}
      {(region === false || region === '') && <Row className='match-height'>
        <Col sm='12'>
          <EjesMultiples titulo={`Venta anual de todas las zonas: ${anio} vs. ${anio - 1} y Objetivo`} tituloAPI='Venta anual de todas las zonas: $anioActual vs. $anioAnterior y Objetivo' formato='moneda' yLabel='Pesos' region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion}  anio={anio} />
        </Col>
      </Row>}
      {(region === false || region === '') && <Row className='match-height'>
        <Col sm='12'>
          <EjesMultiples titulo={`Venta mensual de todas las zonas: ${anio} vs. ${anio - 1} y Objetivo`} tituloAPI='Venta mensual de todas las zonas: $anioActual vs. $anioAnterior y Objetivo' formato='moneda' yLabel='Pesos' region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion}  anio={anio} />
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col sm='12'>
          <Tabla quitarBusqueda={true} titulo='Venta del mes por Departamento o Sub Departamento' subtitulo='Acumulado del mes' formato='moneda' yLabel='Pesos' region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion} opcionesPaginacion={[10, 15, 20]} anio={anio} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <Tabla quitarBusqueda={true} titulo='Venta diaria por Departamento o Sub Departamento' subtitulo='Acumulado del mes' formato='moneda' yLabel='Pesos' region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion} opcionesPaginacion={[10, 15, 20]} anio={anio}  />
        </Col>
      </Row>
      {(tienda === false || tienda === '') && <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo={`Venta anual por tienda: ${anio} vs. ${anio - 1} y Objetivo`} tituloAPI='Venta anual por tienda: $anioActual vs. $anioAnterior y Objetivo' formato='moneda' yLabel='Pesos' region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion} anio={anio} />
        </Col>
      </Row>}
    </>
  )
}
export default VentaSinImpuesto
