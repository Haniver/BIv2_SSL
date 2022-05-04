import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import Tarjeta from '../componentes/auxiliares/Tarjeta'
import fechas_srv from '../services/fechas_srv'
import EjesMultiples from '../componentes/graficos/EjesMultiples'
import EjesMultiplesApilados from '../componentes/graficos/EjesMultiplesApilados'
import Tabla from '../componentes/tablas/Tabla'
import Pie from '../componentes/graficos/Pie'


const Temporada = () => {
    
    const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
    
    const seccion = 'Temporada'

  return (
    <>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro fechas={fechas} setFechas={setFechas} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
            <EjesMultiplesApilados seccion={seccion} titulo='Pedidos Levantados Hoy' fechas={fechas} />
        </Col>
      </Row>
    </>
  )
}
export default Temporada
