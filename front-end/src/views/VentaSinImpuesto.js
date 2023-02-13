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
  const [canal, setCanal] = useState(1)
  const [depto, setDepto] = useState('')
  const [subDepto, setSubDepto] = useState('')
  const [fechas, setFechas] = useState({fecha_ini: '', fecha_fin: fechas_srv.noUTC(new Date())})
  const [anio, setAnio] = useState(fechas_srv.anioActual())
  const [mes, setMes] = useState(fechas_srv.mesActual())
  const [dia, setDia] = useState(fechas_srv.diaActual())
  const [tarjetasCombinadasMes, setTarjetasCombinadasMes] = useState('cargando')
  const [tarjetasCombinadasAnio, setTarjetasCombinadasAnio] = useState('cargando')
  const [tarjetasCombinadasMesAlDia, setTarjetasCombinadasMesAlDia] = useState('cargando')
  const [botonEnviar, setBotonEnviar] = useState(0)

  // console.log(`fechas_srv.ultimoDiaVencidoDelMesReal(anio, mes): ${fechas_srv.ultimoDiaVencidoDelMesReal(anio, mes)}`)

  const seccion = 'VentaSinImpuesto'

  useEffect(() => {
    // console.log("Fechas desde el useEffect:")
    // console.log(fechas)
  }, [fechas])

  return (
    <>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro anio={anio} mes={mes} fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} setAnio={setAnio} setMes={setMes} setFechas={setFechas} setRegion={setRegion} setZona={setZona} setTienda={setTienda} setCanal={setCanal} setDepto={setDepto} setSubDepto={setSubDepto} botonEnviar={botonEnviar} setBotonEnviar={setBotonEnviar} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <Leyenda seccion={seccion} titulo='Última actualización:' />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <IndicadoresEnBarras seccion={seccion} formato='moneda' titulo='Indicadores de Venta' cols={{ xl: '4', sm: '6' }} fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto}/>
          {/* <TarjetaEnFila seccion={seccion} formato='moneda' titulo='Indicadores de Venta' cols={{ xl: '4', sm: '6' }} fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto}/> */}
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <EjesMultiples titulo={`Venta anual por mes: ${anio} vs. ${anio - 1} y Objetivo`} tituloAPI='Venta anual por mes: $anioActual vs. $anioAnterior y Objetivo' formato='moneda' yLabel='Pesos' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} seccion={seccion} />
        </Col>
      </Row>
      {(tienda === false || tienda === '') && <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo={`Venta anual por mes: ${anio} vs. ${anio - 1} y Objetivo`} tituloAPI='Venta anual por mes: $anioActual vs. $anioAnterior y Objetivo' formato='moneda' yLabel='Pesos' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion} />
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col sm='12'>
          <EjesMultiples titulo={`Venta mensual por día: ${anio} vs. ${anio - 1} (fecha comparable) y Objetivo`} tituloAPI='Venta mensual por día: $anioActual vs. $anioAnterior (fecha comparable) y Objetivo' formato='moneda' yLabel='Pesos' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion} quitarCategoriaDeTooltip />
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
          <Tabla quitarBusqueda={true} titulo='Venta sin impuesto por Departamento o Sub Departamento' subtitulo='Acumulado del mes' formato='moneda' yLabel='Pesos' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion} />
        </Col>
      </Row>
      {(tienda === false || tienda === '') && <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo={`Venta anual por tienda: ${anio} vs. ${anio - 1} y Objetivo`} tituloAPI='Venta anual por tienda: $anioActual vs. $anioAnterior y Objetivo' formato='moneda' yLabel='Pesos' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion} />
        </Col>
      </Row>}
    </>
  )
}
export default VentaSinImpuesto
