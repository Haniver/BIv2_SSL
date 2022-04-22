import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import Tarjeta from '../componentes/auxiliares/Tarjeta'
import fechas_srv from '../services/fechas_srv'
import Pie from '../componentes/graficos/Pie'
import ColumnasDrilldown from '../componentes/graficos/ColumnasDrilldown'
import Tabla from '../componentes/tablas/Tabla'
import {
  ShoppingCart,
  FileText,
  Search,
  Maximize
} from 'react-feather'

const VentaOmnicanalTab1 = () => {

  const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
  const [region, setRegion] = useState(false)
  const [zona, setZona] = useState(false)
  const [tienda, setTienda] = useState(false)

  const seccion = 'VentaOmnicanal'

  return (
    <Fragment>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro fechas={fechas} region={region} zona={zona} tienda={tienda} setFechas={setFechas} setRegion={setRegion} setZona={setZona} setTienda={setTienda} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col lg='3' sm='12'>
          <Tarjeta icono={<ShoppingCart size={21} />} seccion={seccion} formato='moneda' titulo='Venta Total Tienda en Línea' fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
        <Col lg='3' sm='12'>
          <Tarjeta icono={<FileText size={21} />} seccion={seccion} formato='moneda' titulo='Ticket Promedio' fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
        <Col lg='3' sm='12'>
          <Tarjeta icono={<Maximize size={21} />} seccion={seccion} formato='porcentaje' titulo='Fullfilment Rate' fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
        <Col lg='3' sm='12'>
          <Tarjeta icono={<Search size={21} />} seccion={seccion} formato='porcentaje' titulo='Found Rate' fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col lg='6' sm='12'>
          <Pie titulo='Venta por Canal' seccion={seccion} formato='moneda' fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
        <Col lg='6' sm='12'>
          <Pie titulo='Ticket Promedio por Canal' seccion={seccion} formato='moneda' fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <ColumnasDrilldown titulo='Monto de Venta por Departamento' labelOrdenadas='Monto de Venta' seccion={seccion} formato='moneda' fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo='Detalle de Venta por Día' seccion={seccion} formato='moneda' fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
      </Row>
    </Fragment>
  )
}
export default VentaOmnicanalTab1
