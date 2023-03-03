import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import fechas_srv from '../services/fechas_srv'
import EjesMultiples from '../componentes/graficos/EjesMultiples'
import Tabla from '../componentes/tablas/Tabla'
import ColumnasNps from '../componentes/graficos/ColumnasNps'
import Spiderweb from '../componentes/graficos/Spiderweb'
import userService from '../services/user.service'
import { set } from 'js-cookie'


const Nps = () => {
    
    const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
    const [region, setRegion] = useState(userService.getRegionPorNivel())
    const [zona, setZona] = useState(userService.getZonaPorNivel())
    const [tienda, setTienda] = useState(userService.getTiendaPorNivel())
    const [agrupador, setAgrupador] = useState('semana')
    const [periodo, setPeriodo] = useState({})
    const [periodoLabel, setPeriodoLabel] = useState('')
    const [provLogist, setProvLogist] = useState([])
    const [nps, setNps] = useState('')
    const [botonEnviar, setBotonEnviar] = useState(0)

    const seccion = 'Nps'

    // useEffect(() => {
    //   console.log(`provLogist:`)
    //   console.log(provLogist)
    //   console.log(`periodo.mes:`)
    //   console.log(periodo.mes)
    //   console.log(`periodo.semana:`)
    //   console.log(periodo.semana)
    // }, [provLogist, periodo])

  return (
    <>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro fechas={fechas} provLogist={provLogist} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} periodoLabel={periodoLabel} nps={nps} setFechas={setFechas}  setProvLogist={setProvLogist} setRegion={setRegion} setZona={setZona} setTienda={setTienda} setAgrupador={setAgrupador} setPeriodo={setPeriodo} setPeriodoLabel={setPeriodoLabel} setNps={setNps} botonEnviar={botonEnviar} setBotonEnviar={setBotonEnviar} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='6'>
          <Tabla quitarPaginacion quitarBusqueda titulo='Evaluación NPS por Día' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} seccion={seccion} provLogist={provLogist} />
        </Col>
        <Col sm='12' lg='6'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <EjesMultiples titulo='NPS por Periodo' fechas={fechas} provLogist={provLogist} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='4'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <ColumnasNps provLogist={provLogist} tituloAPI='Distribución de clientes por calificación' titulo={`Distribución de clientes por calificación 🌒 ${periodoLabel}`} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
        <Col sm='12' lg='4'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <Spiderweb provLogist={provLogist} tituloAPI='Respuestas por responsable' titulo={`Respuestas por responsable 🌒 ${periodoLabel}`} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
        <Col sm='12' lg='4'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <EjesMultiples tituloAPI='NPS por lugar' titulo={`NPS por lugar 🌒 ${periodoLabel}`} fechas={fechas} provLogist={provLogist} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='6'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <Tabla quitarBusqueda quitarExportar tituloAPI='Top 20 respuestas Promotores' titulo={`Top 20 respuestas Promotores 🌒 ${periodoLabel}`} opcionesPaginacion={[5, 20]} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} provLogist={provLogist} />}
        </Col>
        <Col sm='12' lg='6'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <Tabla quitarBusqueda quitarExportar tituloAPI='Top 20 respuestas Pasivos y Detractores' titulo={`Top 20 respuestas Pasivos y Detractores 🌒 ${periodoLabel}`} opcionesPaginacion={[5, 20]} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} provLogist={provLogist} />}
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='6'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <EjesMultiples tituloAPI='Percepción del servicio (n)' titulo={`Percepción del servicio (n) 🌒 ${periodoLabel}`} fechas={fechas} provLogist={provLogist} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
        <Col sm='12' lg='6'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <EjesMultiples tituloAPI='Percepción del servicio (%)' titulo={`Percepción del servicio (%) 🌒 ${periodoLabel}`} fechas={fechas} provLogist={provLogist} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='6'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && nps && <EjesMultiples tituloAPI='Percepción del servicio (n) $categoria' titulo={`Percepción del servicio (n) 🌒 ${periodoLabel} 🔈 ${nps}`} fechas={fechas} provLogist={provLogist} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} nps={nps} seccion={seccion} />}
        </Col>
        <Col sm='12' lg='6'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && nps && <EjesMultiples tituloAPI='Percepción del servicio (%) $categoria' titulo={`Percepción del servicio (%) 🌒 ${periodoLabel} 🔈 ${nps}`} fechas={fechas} provLogist={provLogist} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} nps={nps} seccion={seccion} />}
        </Col>
      </Row>
      <Row className='match-height'>
        {/* <Col sm='12' lg='6'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <EjesMultiples tituloAPI='% NPS Con o Sin Aduana' titulo={`% NPS Con o Sin Aduana 🌒 ${periodoLabel}`} fechas={fechas} provLogist={provLogist} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col> */}
        <Col sm='12'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <EjesMultiples tituloAPI='% NPS por Formato Tienda' titulo={`% NPS por Formato Tienda 🌒 ${periodoLabel}`} fechas={fechas} provLogist={provLogist} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} />}
        </Col>
      </Row>
      <Row className='match-height'>        
        <Col sm='12'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <Tabla tituloAPI='Resumen NPS por tienda' titulo={`Resumen NPS por tienda ${periodoLabel}`} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} provLogist={provLogist} />}
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          {(periodo.mes !== undefined || periodo.semana !== undefined) && <Tabla tituloAPI='Detalle Encuesta NPS'  titulo={`Detalle Encuesta NPS ${periodoLabel}`} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} periodo={periodo} seccion={seccion} provLogist={provLogist} />}
        </Col>
      </Row>
    </>
  )
}
export default Nps
