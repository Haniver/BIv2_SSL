import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import Tarjeta from '../componentes/auxiliares/Tarjeta'
import fechas_srv from '../services/fechas_srv'
import EjesMultiples from '../componentes/graficos/EjesMultiples'
import EjesMultiplesConEscala from '../componentes/graficos/EjesMultiplesConEscala'
import Tabla from '../componentes/tablas/Tabla'
import ColumnasApiladas from '../componentes/graficos/ColumnasApiladas'
import BarrasApiladas from '../componentes/graficos/BarrasApiladas'
import userService from '../services/user.service'
// import userService from '../services/user.service'

const OnTimeInFull = () => {
    
    const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
    const [agrupador, setAgrupador] = useState('semana')
    const [periodo, setPeriodo] = useState({})
    const [region, setRegion] = useState(userService.getRegionPorNivel())
    const [zona, setZona] = useState(userService.getZonaPorNivel())
    const [tienda, setTienda] = useState(userService.getTiendaPorNivel())
    const [sibling, setSibling] = useState(false)
    const [labelTienda, setLabelTienda] = useState(false)
    const [quitarBusqueda, setQuitarBusqueda] = useState(false)
    const [quitarPaginacion, setQuitarPaginacion] = useState(false)
    // const [sufijoTituloTabla, setSufijoTituloTabla] = useState('')
    // const [prefijoTituloTabla, setPrefijoTituloTabla] = useState('')
    const [botonEnviar, setBotonEnviar] = useState(0)

    const seccion = 'OnTimeInFull'


    useEffect(() => {
      // console.log(`Ahora tienda es la ${tienda}`)
      if (!tienda) {
        setQuitarBusqueda(false)
        setQuitarPaginacion(false)
        setSibling(false)
        // setPrefijoTituloTabla('50 tiendas con ')
        // setSufijoTituloTabla(' más bajo')
      } else {
        setQuitarBusqueda(true)
        setQuitarPaginacion(true)
        setSibling({
          region: {
            value: region
          },
          zona: {
            value: zona
          },
          tienda: {
            value: tienda,
            label: labelTienda
          }
        })
      }
      // console.log(`Sibling:`)
      // console.log(sibling)
    }, [tienda])
    
    useEffect(() => {
      if (sibling) {
        // console.log(`Poniendo labelTienda en ${sibling.tienda.label}`)
        setLabelTienda(sibling.tienda.label)
      }
    }, [sibling])

    // useEffect(() => {
    //   console.log(`labelTienda: ${labelTienda}`)
    // }, [labelTienda])

  return (
    <>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro fechas={fechas} agrupador={agrupador} periodo={periodo} region={region} zona={zona} tienda={tienda} sibling={sibling} setFechas={setFechas} setAgrupador={setAgrupador} setPeriodo={setPeriodo} setRegion={setRegion} setZona={setZona} setTienda={setTienda} setLabelTienda={setLabelTienda} botonEnviar={botonEnviar} setBotonEnviar={setBotonEnviar} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='6'>
          <EjesMultiples titulo='Pedidos A Tiempo y Completos' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} seccion={seccion} />
        </Col>
        <Col sm='12' lg='6'>
          <EjesMultiples titulo='Evaluación por KPI A Tiempo y Completo' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='4'>
          <ColumnasApiladas titulo='Pedidos Completos vs. Incompletos' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} formato='porcentaje' />
        </Col>
        <Col sm='12' lg='4'>
          <EjesMultiplesConEscala titulo='Entrega a Tiempo vs. Fuera de Tiempo' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} yLabel='Porcentaje del Total de Entregados' />
        </Col>
        <Col sm='12' lg='4'>
          <EjesMultiplesConEscala titulo='Proceso con Retraso' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} yLabel='Porcentaje del Total de Retrasados' />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo='Pedidos Fuera de Tiempo' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />
        </Col>
      </Row>
      {!tienda && <Row className='match-height'>
        <Col sm='12' lg='6'>
          <ColumnasApiladas titulo='Evaluación de KPI A Tiempo y Completo por Lugar' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} formato='porcentaje' />
        </Col>
        <Col sm='12' lg='6'>
          <EjesMultiples titulo='Evaluación A Tiempo y Completo por Lugar' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col sm='12' lg='6'>
          <EjesMultiples titulo='Evaluación por KPI' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />
        </Col>
        <Col sm='12' lg='6'>
          <ColumnasApiladas titulo='Pedidos por Tipo de Entrega' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} formato='entero' />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo='Tiendas por % A Tiempo y Completo más bajo' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} setSibling={setSibling} quitarBusqueda={quitarBusqueda} quitarPaginacion={quitarPaginacion} />
        </Col>
      </Row>
      {sibling && <Row className='match-height'>
        <Col sm='12'>
          <Tabla tituloAPI='$Tienda' titulo={labelTienda} fechas={fechas} region={sibling.region.value} zona={sibling.zona.value} tienda={sibling.tienda.value} agrupador={agrupador} periodo={periodo} seccion={seccion} />
        </Col>
      </Row>}
    </>
  )
}
export default OnTimeInFull
