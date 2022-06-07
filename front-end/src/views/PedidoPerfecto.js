import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import Tarjeta from '../componentes/auxiliares/Tarjeta'
import fechas_srv from '../services/fechas_srv'
import EjesMultiples from '../componentes/graficos/EjesMultiples'
import Tabla from '../componentes/tablas/Tabla'
import ColumnasApiladas from '../componentes/graficos/ColumnasApiladas'
import BarrasApiladas from '../componentes/graficos/BarrasApiladas'
import userService from '../services/user.service'

const PedidoPerfecto = () => {
    
    const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
    const [agrupador, setAgrupador] = useState('semana')
    const [periodo, setPeriodo] = useState({})
    const [region, setRegion] = useState('')
    const [zona, setZona] = useState('')
    const [tienda, setTienda] = useState('')
    const [sibling, setSibling] = useState(false)
    const [labelTienda, setLabelTienda] = useState(false)
    const [quitarBusqueda, setQuitarBusqueda] = useState(false)
    const [quitarPaginacion, setQuitarPaginacion] = useState(false)
    const [sufijoTituloTabla, setSufijoTituloTabla] = useState('')
    const [prefijoTituloTabla, setPrefijoTituloTabla] = useState('')

    const seccion = 'PedidoPerfecto'


    useEffect(() => {
      if (!tienda) {
        setQuitarBusqueda(false)
        setQuitarPaginacion(false)
        setPrefijoTituloTabla('50 tiendas con ')
        setSufijoTituloTabla(' más bajo')
      } else {
        setQuitarBusqueda(true)
        setQuitarPaginacion(true)
        setPrefijoTituloTabla('')
        setSufijoTituloTabla('')
      }
    }, [tienda])
    

  return (
    <>
      {userService.getNivel() <= 3 && <Row className='match-height'>
        <Col sm='12'>
          <h2 className='centrado'>{userService.getLugarNombre()}</h2>
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro fechas={fechas} agrupador={agrupador} periodo={periodo} region={region} zona={zona} tienda={tienda} sibling={sibling} setFechas={setFechas} setAgrupador={setAgrupador} setPeriodo={setPeriodo} setRegion={setRegion} setZona={setZona} setTienda={setTienda} setLabelTienda={setLabelTienda} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='5'>
          <EjesMultiples titulo='Pedidos Perfectos' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} seccion={seccion} />
        </Col>
        <Col sm='12' lg='4'>
          <EjesMultiples titulo='Evaluación por KPI Pedido Perfecto' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />
        </Col>
        <Col sm='12' lg='3'>
          <EjesMultiples titulo='Evaluación por KPI' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />
        </Col>
      </Row>
      {!tienda && <Row className='match-height'>
        <Col sm='12' lg='6'>
          <ColumnasApiladas titulo='Evaluación de KPI Pedido Perfecto por Lugar' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} formato='porcentaje' />
        </Col>
        <Col sm='12' lg='6'>
          <EjesMultiples titulo='Evaluación Pedido Perfecto por Lugar' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col sm='12' lg='6'>
          <EjesMultiples titulo='Motivos de Quejas' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />
        </Col>
        <Col sm='12' lg='6'>
          <ColumnasApiladas titulo='Pedidos por Tipo de Entrega' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} formato='entero' />
        </Col>
      </Row>
      {!tienda && <Row className='match-height'>
        <Col sm='12' lg='6'>
          <BarrasApiladas tituloAPI='Quejas por lugar $periodo1' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} formato='entero' />
        </Col>
        <Col sm='12' lg='6'>
          <BarrasApiladas tituloAPI='Quejas por lugar $periodo2' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} formato='entero' />
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col sm='12'>
          <Tabla tituloAPI='50 Tiendas con % Pedido Perfecto más bajo' titulo={`${prefijoTituloTabla}% Pedido Perfecto${sufijoTituloTabla}`} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} setSibling={setSibling} quitarBusqueda={quitarBusqueda} quitarPaginacion={quitarPaginacion} />
        </Col>
      </Row>
      {tienda !== undefined && tienda !== '' && <Row className='match-height'>
        <Col sm='12'>
          <Tabla tituloAPI='$Tienda' titulo={labelTienda} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />
        </Col>
      </Row>}
    </>
  )
}
export default PedidoPerfecto
