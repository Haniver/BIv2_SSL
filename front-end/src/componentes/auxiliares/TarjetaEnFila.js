// ** Third Party Components
// import PropTypes from 'prop-types'
import authHeader from '../../services/auth.header'
import axios from 'axios'
import { useState, useEffect, useReducer } from 'react'
import CustomUrls from '../../services/customUrls'
import LoadingGif from '../auxiliares/LoadingGif'
import fechas_srv from '../../services/fechas_srv'
import classnames from 'classnames'
// ** Third Party Components
import { 
  TrendingUp, 
  User, 
  Box, 
  DollarSign,
  FileText,
  Percent,
  Package,
  Calendar,
  Target,
  Divide,
  DivideCircle,
  FastForward,
  Navigation2,
  PieChart
} from 'react-feather'

// ** Custom Components
import Avatar from '@components/avatar'

// ** Reactstrap Imports
import { Card, CardHeader, CardTitle, CardBody, CardText, Row, Col } from 'reactstrap'


const TarjetaEnFila = ({ cols, icono, titulo, tituloAPI, seccion, className, formato, fechas, region, zona, tienda, proveedor, depto, subDepto, canal, anioRFM, mesRFM, resAPI, colorPositivo }) => {
  const [estadoLoader, dispatchLoader] = useReducer((estadoLoader, accion) => {
    switch (accion.tipo) {
      case 'llamarAPI':
        return { contador: estadoLoader.contador + 1 }
      case 'recibirDeAPI':
        return { contador: estadoLoader.contador - 1 }
      default:
        throw new Error()
    }
  }, {contador: 0})

  const tituloEnviar = (tituloAPI) ? tituloAPI : titulo // Como la API usa el título de la tarjeta para regresar su valor, había un problema cuando ese título es variable, como cuando incluye la fecha actual. Entonces, si desde la vista le mandas el prop tituloAPI, es ese el que se usa para la API. Si lo omites, se usa la variable titulo como estaba pensado originalmente

  const queCambiar = (resAPI === undefined) ? [fechas, region, zona, tienda, canal, depto, subDepto, mesRFM, anioRFM] : [resAPI]

  const iconos = {
    TrendingUp, 
    User, 
    Box, 
    DollarSign,
    FileText,
    Percent,
    Package,
    Calendar,
    Target,
    Divide,
    DivideCircle,
    FastForward,
    Navigation2,
    PieChart
  }
  const [data, setData] = useState([
    {
      valor: '230k',
      titulo: 'Sales',
      color: 'light-primary',
      icon: <TrendingUp size={18} />
    },
    {
      valor: '8.549k',
      titulo: 'Customers',
      color: 'light-info',
      icon: <User size={18} />
    },
    {
      valor: '1.423k',
      titulo: 'Products',
      color: 'light-danger',
      icon: <Box size={18} />
    },
    {
      valor: '$9745',
      titulo: 'Revenue',
      color: 'light-success',
      icon: <DollarSign size={18} />
    }
  ])

  useEffect(async () => {
    let resultado_tmp = 3.1416
    let hayResultados = 'no'
    if (resAPI !== undefined) {
      if (resAPI !== 'cargando') {
        resultado_tmp = resAPI.res[tituloEnviar]
        hayResultados = resAPI.hayResultados
      }
    } else {
      dispatchLoader({tipo: 'llamarAPI'})
      const res = await axios({
        method: 'post',
        url: `${CustomUrls.ApiUrl()}tarjetasEnFila/${seccion}?titulo=${tituloEnviar}`,
        headers: authHeader(),
        data: {
          fechas,
          region,
          zona,
          tienda,
          depto,
          subDepto,
          proveedor,
          canal,
          anioRFM,
          mesRFM
        }
      })
      // Wawa aquí te quedaste. Ver ClickUp para pendientes
      resultado_tmp = res.data.res
      dispatchLoader({tipo: 'recibirDeAPI'})
    }
    resultado_tmp.forEach(resultado => {
      if (resultado.formato === 'moneda') {
        const formatoMoneda = new Intl.NumberFormat('es-MX', {
          style: 'currency',
          currency: 'MXN'
        })
        resultado.valor = formatoMoneda.format(resultado.valor)
      } else if (resultado.formato === 'porcentaje') {
        const formatoPorcentaje = new Intl.NumberFormat('es-MX', {
          style: 'percent',
          minimumFractionDigits: 2,
          maximumFractionDigits: 2
        })
        resultado.valor = formatoPorcentaje.format(resultado.valor)
      } else if (resultado.formato === 'entero') {
        const formatoEntero = new Intl.NumberFormat('es-MX', {
          maximumFractionDigits: 0
        })
        resultado.valor = formatoEntero.format(resultado.valor)
      }
      const Icono = iconos[resultado.icon]
      resultado.icon = <Icono size={18} />
      // console.log(`Query ${titulo}:\n${JSON.stringify(res.data.pipeline)}`)
    })
    setData(resultado_tmp)
  }, queCambiar)

  const renderData = () => {
    return data.map((item, index) => {
      const colMargin = Object.keys(cols)
      const margin = index === 2 ? 'sm' : colMargin[0]
      return (
        <Col
        key={index}
        {...cols}
        className={classnames({
          [`mb-2 mb-${margin}-0`]: index !== data.length - 1
        })}
      >
        <div className='d-flex align-items-center'>
          <Avatar icon={item.icon} className='avatar p-50 m-0 mb-1 bg-light-primary mr-1' />
          <div className='my-auto'>
            <h4 className='fw-bolder mb-0'>{item.valor}</h4>
            <CardText className='font-small-3 mb-0'>{item.titulo}</CardText>
          </div>
        </div>
      </Col>
      )
    })
  }

  return (
    <Card>
      <CardBody className={className}>
    {estadoLoader.contador === 0 && resAPI !== 'cargando' && 
        <Row>{renderData()}</Row>}
    {(estadoLoader.contador !== 0 || resAPI === 'cargando') && <LoadingGif />}
      </CardBody>
    </Card>
  )
}

export default TarjetaEnFila
