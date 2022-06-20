import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import Tarjeta from '../componentes/auxiliares/Tarjeta'
import fechas_srv from '../services/fechas_srv'
import EjesMultiples from '../componentes/graficos/EjesMultiples'
import Tabla from '../componentes/tablas/Tabla'
import tarjetasCombinadas from '../services/tarjetasCombinadas'
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

  const [region, setRegion] = useState(false)
  const [zona, setZona] = useState(false)
  const [tienda, setTienda] = useState(false)
  const [canal, setCanal] = useState(false)
  const [depto, setDepto] = useState(false)
  const [subDepto, setSubDepto] = useState(false)
  const [fechas, setFechas] = useState({fecha_ini: '', fecha_fin: fechas_srv.actualVencida()})
  const [anio, setAnio] = useState(fechas_srv.anioActual())
  const [mes, setMes] = useState(fechas_srv.mesActual())
  const [dia, setDia] = useState(fechas_srv.diaActual())
  const [tarjetasCombinadasMes, setTarjetasCombinadasMes] = useState('cargando')
  const [tarjetasCombinadasAnio, setTarjetasCombinadasAnio] = useState('cargando')
  const [tarjetasCombinadasMesAlDia, setTarjetasCombinadasMesAlDia] = useState('cargando')

  const seccion = 'VentaSinImpuesto'

  useEffect(async () => {
    setTarjetasCombinadasAnio('cargando')
    setTarjetasCombinadasMes('cargando')
    setTarjetasCombinadasMesAlDia('cargando')
    const resAnio = await tarjetasCombinadas(seccion, 'Anio', {
        fechas, 
        region, 
        zona, 
        tienda, 
        canal, 
        depto, 
        subDepto
    })
    setTarjetasCombinadasAnio(resAnio)
    const resMes = await tarjetasCombinadas(seccion, 'Mes', {
        fechas, 
        region, 
        zona, 
        tienda, 
        canal, 
        depto, 
        subDepto
    })
    setTarjetasCombinadasMes(resMes)
    const resMesAlDia = await tarjetasCombinadas(seccion, 'MesAlDia', {
        fechas, 
        region, 
        zona, 
        tienda, 
        canal, 
        depto, 
        subDepto
    })
    setTarjetasCombinadasMesAlDia(resMesAlDia)
  }, [fechas, region, zona, tienda, canal, depto, subDepto])

  useEffect(() => {
    console.log(`fecha_fin: ${fechas.fecha_fin}`)
    console.log(`mesTexto: ${fechas_srv.mesTexto(mes)}`)

  }, [fechas])

  return (
    <>
      {/* {userService.getNivel() <= 3 && <Row className='match-height'>
        <Col sm='12'>
          <h2 className='centrado'>{userService.getLugarNombre()}</h2>
        </Col>
      </Row>} */}
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro anio={anio} mes={mes} fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} setAnio={setAnio} setMes={setMes} setFechas={setFechas} setRegion={setRegion} setZona={setZona} setTienda={setTienda} setCanal={setCanal} setDepto={setDepto} setSubDepto={setSubDepto} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col>
          <Tarjeta icono={<DollarSign size={21} />} formato='moneda' titulo={`Venta ${anio}`} tituloAPI='Venta $anio' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} resAPI={tarjetasCombinadasAnio} />
        </Col>
        <Col>
          <Tarjeta icono={<Calendar size={21} />} formato='moneda' titulo={`Venta ${anio - 1} al ${fechas_srv.ultimoDiaVencidoDelMesReal(anio, mes)} de ${fechas_srv.mesTexto(mes)}`} tituloAPI='Venta $anioPasado al $dia de $mes' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} resAPI={tarjetasCombinadasAnio} />
        </Col>
        {(canal === 1 || canal === 35 || canal === 36) && <Col>
          <Tarjeta icono={<Target size={21} />} formato='moneda' titulo={`Objetivo ${anio - 1} al ${fechas_srv.ultimoDiaVencidoDelMesReal(anio, mes)} de ${fechas_srv.mesTexto(mes)}`} tituloAPI='Objetivo $anioActual al $dia de $mes' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto}  resAPI={tarjetasCombinadasAnio} />
        </Col>}
        <Col>
          <Tarjeta icono={<Divide size={21} />} colorPositivo formato='porcentaje' titulo={`Variación ${anio} vs. ${anio - 1}`} tituloAPI='Variación $anioActual vs. $anioAnterior' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} resAPI={tarjetasCombinadasAnio} />
        </Col>
        {(canal === 1 || canal === 35 || canal === 36) && <Col>
          <Tarjeta icono={<DivideCircle size={21} />} colorPositivo formato='porcentaje' titulo={`Variación Objetivo ${anio}`} tituloAPI='Variación Objetivo $anioActual' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto}  resAPI={tarjetasCombinadasAnio} />
        </Col>}
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='3'>
          <Tarjeta icono={<DollarSign size={21} />} formato='moneda' titulo={`Venta ${fechas_srv.mesTexto(mes)} ${anio}`} tituloAPI='Venta $mes $anio' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} resAPI={tarjetasCombinadasMes} />
        </Col>
        <Col sm='12' lg='9'>
          <Row className='match-height'>
              {(canal === 1 || canal === 35 || canal === 36) && <Col>
              <Tarjeta icono={<Target size={21} />} formato='moneda' titulo={`Objetivo ${fechas_srv.mesTexto(mes)} ${anio}`} tituloAPI='Objetivo $mes $anio' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} resAPI={tarjetasCombinadasMes} />
            </Col>}
            <Col>
              <Tarjeta icono={<FastForward size={21} />} formato='moneda' titulo={`Proyección ${fechas_srv.mesTexto(mes)} ${anio}`} tituloAPI='Proyección $mes $anio' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} resAPI={tarjetasCombinadasMes} />
            </Col>
            {(canal === 1 || canal === 35 || canal === 36) && <Col>
              <Tarjeta icono={<Navigation2 size={21} />} colorPositivo formato='porcentaje' titulo={`Avance ${fechas_srv.mesTexto(mes)} ${anio}`} tituloAPI='Avance $mes $anio' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} resAPI={tarjetasCombinadasMes} />
            </Col>}
            {(canal === 1 || canal === 35 || canal === 36) && <Col>
              <Tarjeta icono={<PieChart size={21} />} colorPositivo formato='porcentaje' titulo={`Alcance ${fechas_srv.mesTexto(mes)} ${anio}`} tituloAPI='Alcance $mes $anio' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} resAPI={tarjetasCombinadasMes} />
            </Col>}
          </Row>
          <Row className='match-height'>
            <Col>
              <Tarjeta icono={<Target size={21} />} formato='moneda' titulo={`Objetivo del 1 al ${fechas_srv.ultimoDiaVencidoDelMesReal(anio, mes)} de ${fechas_srv.mesTexto(mes)} ${anio}`} tituloAPI='Objetivo 1 al $dia $mes $anio' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} resAPI={tarjetasCombinadasMesAlDia} />
            </Col>
            <Col>
              <Tarjeta icono={<Navigation2 size={21} />} colorPositivo formato='porcentaje' titulo={`Objetivo Vs. Venta al ${fechas_srv.ultimoDiaVencidoDelMesReal(anio, mes)} de ${fechas_srv.mesTexto(mes)} ${anio}`} tituloAPI='Objetivo Vs. Venta al $dia $mes $anio' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} resAPI={tarjetasCombinadasMesAlDia} />
            </Col>
            <Col>
              <Tarjeta icono={<Calendar size={21} />} formato='moneda' titulo={`Venta del 1 al ${fechas_srv.ultimoDiaVencidoDelMesReal(anio, mes)} de ${fechas_srv.mesTexto(mes)} ${anio - 1}`} tituloAPI='Venta 1 al $dia $mes $anioAnterior' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} resAPI={tarjetasCombinadasMesAlDia} />
            </Col>
            <Col>
              <Tarjeta icono={<DivideCircle size={21} />} colorPositivo formato='porcentaje' titulo={`Venta ${anio - 1} Vs. ${anio} al ${fechas_srv.ultimoDiaVencidoDelMesReal(anio, mes)} de ${fechas_srv.mesTexto(mes)}`} tituloAPI='Venta $anioAnterior Vs. $anioActual al $dia $mes' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} resAPI={tarjetasCombinadasMesAlDia} />
            </Col>
          </Row>
        </Col>
      </Row>
        <Col>
           <Tarjeta icono={<DollarSign size={21} />} formato='moneda' titulo={`Venta del 1 al ${fechas_srv.ultimoDiaVencidoDelMesReal(anio, mes)} de ${fechas_srv.mesTexto(mes)} ${anio}`} tituloAPI='Venta 1 al $dia $mes $anioActual' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} resAPI={tarjetasCombinadasMesAlDia} />
        </Col>
      <Row className='match-height'>
        <Col sm='12'>
          <EjesMultiples titulo={`Venta anual por mes: ${anio} vs. ${anio - 1} y Objetivo`} tituloAPI='Venta anual por mes: $anioActual vs. $anioAnterior y Objetivo' formato='moneda' yLabel='Pesos' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} seccion={seccion} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <EjesMultiples titulo={`Venta mensual por día: ${anio} vs. ${anio - 1} y Objetivo`} tituloAPI='Venta mensual por día: $anioActual vs. $anioAnterior y Objetivo' formato='moneda' yLabel='Pesos' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion} />
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
          <Tabla quitarBusqueda={true} titulo='Venta sin impuesto por Departamento o Sub Departamento' formato='moneda' yLabel='Pesos' fechas={fechas} region={region} zona={zona} tienda={tienda} canal={canal} depto={depto} subDepto={subDepto} mes={mes} seccion={seccion} />
        </Col>
      </Row>
    </>
  )
}
export default VentaSinImpuesto
