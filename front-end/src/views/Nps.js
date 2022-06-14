import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import fechas_srv from '../services/fechas_srv'
import EjesMultiples from '../componentes/graficos/EjesMultiples'
import Tabla from '../componentes/tablas/Tabla'
import ColumnasNps from '../componentes/graficos/ColumnasNps'
import Spiderweb from '../componentes/graficos/Spiderweb'
import { set } from 'js-cookie'


const Nps = () => {
    
    const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
    const [region, setRegion] = useState(false)
    const [zona, setZona] = useState(false)
    const [tienda, setTienda] = useState(false)
    const [agrupador, setAgrupador] = useState('dia')
    const [periodo, setPeriodo] = useState({})
    const [periodoLabel, setPeriodoLabel] = useState('')
    const [nps, setNps] = useState('')

    const seccion = 'Nps'

    useEffect(() => {
      console.log(`Categoría NPS: ${nps}`)
    }, [nps])
    

  return (
    <>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} periodoLabel={periodoLabel} nps={nps} setFechas={setFechas} setRegion={setRegion} setZona={setZona} setTienda={setTienda} setAgrupador={setAgrupador} setPeriodo={setPeriodo} setPeriodoLabel={setPeriodoLabel} setNps={setNps} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='6'>
          <Tabla quitarPaginacion quitarBusqueda titulo='Evaluación NPS por Día' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} seccion={seccion} />
        </Col>
        <Col sm='12' lg='6'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <EjesMultiples titulo='NPS por Día' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='4'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <ColumnasNps tituloAPI='Distribución de clientes por calificación' titulo={`Distribución de clientes por calificación 🌒 ${periodoLabel}`} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
        <Col sm='12' lg='4'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <Spiderweb tituloAPI='Respuestas por responsable' titulo={`Respuestas por responsable 🌒 ${periodoLabel}`} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
        <Col sm='12' lg='4'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <EjesMultiples tituloAPI='NPS por lugar' titulo={`NPS por lugar 🌒 ${periodoLabel}`} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='6'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <Tabla quitarBusqueda quitarExportar tituloAPI='Top 20 respuestas Promotores' titulo={`Top 20 respuestas Promotores 🌒 ${periodoLabel}`} opcionesPaginacion={[5, 20]} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
        <Col sm='12' lg='6'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <Tabla quitarBusqueda quitarExportar tituloAPI='Top 20 respuestas Pasivos y Detractores' titulo={`Top 20 respuestas Pasivos y Detractores 🌒 ${periodoLabel}`} opcionesPaginacion={[5, 20]} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='6'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <EjesMultiples tituloAPI='Percepción del servicio (n)' titulo={`Percepción del servicio (n) 🌒 ${periodoLabel}`} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
        <Col sm='12' lg='6'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <EjesMultiples tituloAPI='Percepción del servicio (%)' titulo={`Percepción del servicio (%) 🌒 ${periodoLabel}`} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='6'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <EjesMultiples tituloAPI='Percepción del servicio (n) $categoria' titulo={`Percepción del servicio (n) 🌒 ${periodoLabel} 🔈 ${nps}`} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} nps={nps} seccion={seccion} />}
        </Col>
        <Col sm='12' lg='6'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <EjesMultiples tituloAPI='Percepción del servicio (%) $categoria' titulo={`Percepción del servicio (%) 🌒 ${periodoLabel} 🔈 ${nps}`} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} nps={nps} seccion={seccion} />}
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='6'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <EjesMultiples tituloAPI='% NPS Con o Sin Aduana' titulo={`% NPS Con o Sin Aduana 🌒 ${periodoLabel}`} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
        <Col sm='12' lg='6'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <EjesMultiples tituloAPI='% NPS por Formato Tienda' titulo={`% NPS por Formato Tienda 🌒 ${periodoLabel}`} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
      </Row>
      <Row className='match-height'>        
        <Col sm='12'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <Tabla tituloAPI='Tiendas por NPS Más Bajo' titulo={`Tiendas por NPS Más Bajo 🌒 ${periodoLabel}`} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <Tabla tituloAPI='Comentarios y Calificación Encuesta NPS'  titulo={`Comentarios y Calificación Encuesta NPS 🌒 ${periodoLabel}`} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
      </Row>
    </>
  )
}
export default Nps
