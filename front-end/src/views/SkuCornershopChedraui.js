import { useState, useEffect } from 'react'
import { Row, Col } from 'reactstrap'
import fechas_srv from '../services/fechas_srv'
import Tabla from '../componentes/tablas/Tabla'
import Filtro from '../componentes/auxiliares/Filtro'
import userService from '../services/user.service'
// import userService from '../services/user.service'

const SkuCornershopChedraui = () => {
    const [fechas, setFechas] = useState({
        fecha_ini: fechas_srv.actualVencida(),
        fecha_fin: fechas_srv.actualVencida()
    })
    const [region, setRegion] = useState(userService.getRegionPorNivel())
    const [zona, setZona] = useState(userService.getZonaPorNivel())
    const [tienda, setTienda] = useState(userService.getTiendaPorNivel())
    const [canal2, setCanal2] = useState('')
    const [depto, setDepto] = useState('')
    const [subDepto, setSubDepto] = useState('')
    const [e3, setE3] = useState('')
    const [botonEnviar, setBotonEnviar] = useState(0)

    const seccion = 'SkuCornershopChedraui'

    // useEffect(() => {
    //     console.log(`Fechas desde parent:`)
    //     console.log(fechas)
    //     console.log(`region: ${region}`)
    //     console.log(`zona: ${zona}`)
    //     console.log(`tienda: ${tienda}`)
    //     console.log(`depto: ${depto}`)
    //     console.log(`subDepto: ${subDepto}`)
    //     console.log(`e3: ${e3}`)
    //     console.log(`canal2: ${canal2}`)
    // }, [fechas])

  return (
    <>
      {/* {userService.getNivel() <= 3 && <Row className='match-height'>
        <Col sm='12'>
          <h2 className='centrado'>{userService.getLugarNombre()}</h2>
        </Col>
      </Row>} */}
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro botonEnviar={botonEnviar} rango_max_dias={15} fechas={fechas} region={region} zona={zona} tienda={tienda} canal2={canal2} depto={depto} subDepto={subDepto} e3={e3} setFechas={setFechas} setRegion={setRegion} setZona={setZona} setTienda={setTienda} setCanal2={setCanal2} setDepto={setDepto} setSubDepto={setSubDepto} setE3={setE3} setBotonEnviar={setBotonEnviar} />
        </Col>
      </Row>
      <Row className='match-height'>
      {botonEnviar > 0 && <Col sm='12'>
          <Tabla titulo='SKU Cornershop-Chedraui' botonEnviar={botonEnviar} fechas={fechas} region={region} zona={zona} tienda={tienda} canal2={canal2} depto={depto} subDepto={subDepto} e3={e3} seccion={seccion} />
        </Col>}
      </Row>
    </>
  )
}
export default SkuCornershopChedraui
