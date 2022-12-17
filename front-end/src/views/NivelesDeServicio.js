import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import fechas_srv from '../services/fechas_srv'
import ColumnasApiladas from '../componentes/graficos/ColumnasApiladas'
import Pie from '../componentes/graficos/Pie'
import Tabla from '../componentes/tablas/Tabla'
import cargarFiltros from '../services/cargarFiltros'
// import userService from '../services/user.service'

const NivelesDeServicio = () => {
  const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
  const [region, setRegion] = useState('')
  const [zona, setZona] = useState('')
  const [tienda, setTienda] = useState('')
  const [categoria, setCategoria] = useState('')
  const [tipoEntrega, setTipoEntrega] = useState('')
  const [tiendaNombre, setTiendaNombre] = useState('')
  const [botonEnviar, setBotonEnviar] = useState(0)

  const seccion = 'NivelesDeServicio'
  useEffect(async () => {
    if (tienda !== '' && tienda !== undefined && tienda !== '' && tienda !== false) {
      const nombreTienda_tmp = await cargarFiltros.nombreTienda(tienda)
      // console.log("Nombre Tienda:")
      // console.log(nombreTienda_tmp)
      setTiendaNombre(nombreTienda_tmp.data.nombreTienda)
    }
  }, [tienda])

  useEffect(() => {
    console.log(`Tipo de entrega: ${tipoEntrega}`)
  }, [tipoEntrega])

  return (
    <Fragment>
      {/* {userService.getNivel() <= 3 && <Row className='match-height'>
        <Col sm='12'>
          <h2 className='centrado'>{userService.getLugarNombre()}</h2>
        </Col>
      </Row>} */}
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro fechas={fechas} region={region} zona={zona} tienda={tienda} categoria={categoria} tipoEntrega={tipoEntrega} setFechas={setFechas} setRegion={setRegion} setZona={setZona} setTienda={setTienda} setCategoria={setCategoria} setTipoEntrega={setTipoEntrega} botonEnviar={botonEnviar} setBotonEnviar={setBotonEnviar} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col xl={(tienda === '' || tienda === false || tienda === undefined) ? '6' : '12'} sm='12'>
          <Pie titulo='Estatus de Entrega y No Entrega' formato='entero' seccion={seccion} yLabel='Pedidos' fechas={fechas} region={region} zona={zona} tienda={tienda} categoria={categoria} tipoEntrega={tipoEntrega} />
        </Col>
        {(tienda === '' || tienda === false || tienda === undefined) && <Col xl='6' sm='12'>
          <ColumnasApiladas titulo='Estatus de Entrega y No Entrega por Área' seccion={seccion} formato='entero' yLabel='Pedidos' fechas={fechas} region={region} zona={zona} tienda={tienda} categoria={categoria} tipoEntrega={tipoEntrega} />
        </Col>}
      </Row>
      <Row className='match-height'>
        {(tipoEntrega === '' || tipoEntrega === false || tipoEntrega === undefined) && <Col sm='12'>
        <Pie titulo='Pedidos Por Tipo de Entrega' formato='entero' seccion={seccion} yLabel='Pedidos' fechas={fechas} region={region} zona={zona} tienda={tienda} categoria={categoria} tipoEntrega={tipoEntrega} />
        </Col>}
      </Row>
      <Row className='match-height'>
        <Col  xl={(tienda === '' || tienda === false || tienda === undefined) ? '6' : '12'} sm='12'>
          <Pie titulo='Pedidos Cancelados' formato='entero' seccion={seccion} yLabel='Pedidos' fechas={fechas} region={region} zona={zona} tienda={tienda} categoria={categoria} tipoEntrega={tipoEntrega} />
        </Col>
        {(tienda === '' || tienda === false || tienda === undefined) && <Col xl='6' sm='12'>
          <ColumnasApiladas titulo='Pedidos Cancelados por Área' seccion={seccion} formato='entero' yLabel='Pedidos' fechas={fechas} region={region} zona={zona} tienda={tienda} categoria={categoria} tipoEntrega={tipoEntrega} />
        </Col>}
      </Row>
      <Row className='match-height'>
      {(zona === '' || zona === false || zona === undefined) && <Col sm='12'>
          <Tabla titulo='Estatus de Entrega y No Entrega por Área' seccion={seccion} fechas={fechas} region={region} zona={zona} tienda={tienda} categoria={categoria} tipoEntrega={tipoEntrega} />
        </Col>}
      </Row>
      {(tienda === '' || tienda === false || tienda === undefined) && <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo='Estatus de Entrega y No Entrega por Tienda' seccion={seccion} fechas={fechas} region={region} zona={zona} tienda={tienda} categoria={categoria} tipoEntrega={tipoEntrega} />
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col sm='12'>
          <ColumnasApiladas titulo='Estatus de Entrega y No Entrega por Día' seccion={seccion} formato='entero' yLabel='Pedidos' fechas={fechas} region={region} zona={zona} tienda={tienda} categoria={categoria} tipoEntrega={tipoEntrega} />
        </Col>
      </Row>
      {tienda !== '' && tienda !== false && tienda !== undefined && <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo={`Detalle de pedidos ${tiendaNombre}`} tituloAPI='Detalle de pedidos $tienda' seccion={seccion} fechas={fechas} region={region} zona={zona} tienda={tienda} categoria={categoria} tipoEntrega={tipoEntrega} />
        </Col>
      </Row>}
    </Fragment>
  )
}
export default NivelesDeServicio
