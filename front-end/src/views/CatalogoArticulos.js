import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Sankey from '../componentes/graficos/Sankey'
import Filtro from '../componentes/auxiliares/Filtro'
import BarrasApiladas from '../componentes/graficos/BarrasApiladas'
import ColumnasAgrupadasYApiladas from '../componentes/graficos/ColumnasAgrupadasYApiladas'

const CatalogoArticulos = () => {
    
    const [agrupador, setAgrupador] = useState('semana')
    const [grupoDeptos, setGrupoDeptos] = useState('')
    const [deptoAgrupado, setDeptoAgrupado] = useState('')
    const [subDeptoAgrupado, setSubDeptoAgrupado] = useState('')
    const [periodo, setPeriodo] = useState({})
    const [botonEnviar, setBotonEnviar] = useState(0)

    const seccion = 'CatalogoArticulos'

    // useEffect(() => {
    //     console.log(`grupoDeptos = ${grupoDeptos}`)
    //     console.log(`deptoAgrupado = ${deptoAgrupado}`)
    //     console.log(`subDeptoAgrupado = ${subDeptoAgrupado}`)
    // }, [grupoDeptos, deptoAgrupado, subDeptoAgrupado])
    

  return (
    <>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro agrupador={agrupador} agrupadorSinDia periodo={periodo} grupoDeptos={grupoDeptos} deptoAgrupado={deptoAgrupado} subDeptoAgrupado={subDeptoAgrupado} setAgrupador={setAgrupador} setPeriodo={setPeriodo} setGrupoDeptos={setGrupoDeptos} setDeptoAgrupado={setDeptoAgrupado} setSubDeptoAgrupado={setSubDeptoAgrupado} botonEnviar={botonEnviar} setBotonEnviar={setBotonEnviar} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <Sankey titulo='Métricas Básicas' seccion={seccion} agrupador={agrupador} periodo={periodo} grupoDeptos={grupoDeptos} deptoAgrupado={deptoAgrupado} subDeptoAgrupado={subDeptoAgrupado} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='4'>
          <BarrasApiladas titulo='Aprobados y No Aprobados por Departamento' porcentaje seccion={seccion} agrupador={agrupador} periodo={periodo} grupoDeptos={grupoDeptos} deptoAgrupado={deptoAgrupado} />
        </Col>
        <Col sm='12' lg='4'>
          <BarrasApiladas titulo='Porcentaje CMV' porcentaje sinCantidad seccion={seccion} agrupador={agrupador} periodo={periodo} grupoDeptos={grupoDeptos} deptoAgrupado={deptoAgrupado} />
        </Col>
        <Col sm='12' lg='4'>
          <BarrasApiladas titulo='Porcentaje CDB' porcentaje seccion={seccion} agrupador={agrupador} periodo={periodo} grupoDeptos={grupoDeptos} deptoAgrupado={deptoAgrupado} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <ColumnasAgrupadasYApiladas titulo='Comparativo KPI y Departamento' seccion={seccion} agrupador={agrupador} periodo={periodo} grupoDeptos={grupoDeptos} deptoAgrupado={deptoAgrupado} />
        </Col>
      </Row>
    </>
  )
}
export default CatalogoArticulos
