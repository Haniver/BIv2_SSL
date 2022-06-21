// ** Third Party Components
// import PropTypes from 'prop-types'
import { Card, CardBody } from 'reactstrap'
import authHeader from '../../services/auth.header'
import axios from 'axios'
import { useState, useEffect, useReducer } from 'react'
import CustomUrls from '../../services/customUrls'
import LoadingGif from '../auxiliares/LoadingGif'

const Tarjeta = ({ icono, titulo, tituloAPI, seccion, className, formato, fechas, region, zona, tienda, proveedor, depto, subDepto, canal, anioRFM, mesRFM, resAPI, colorPositivo }) => {
  const [numero, setNumero] = useState('')
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

  const titulo_enviar = (tituloAPI) ? tituloAPI : titulo // Como la API usa el título de la tarjeta para regresar su valor, había un problema cuando ese título es variable, como cuando incluye la fecha actual. Entonces, si desde la vista le mandas el prop tituloAPI, es ese el que se usa para la API. Si lo omites, se usa la variable titulo como estaba pensado originalmente

  const [tituloMostrar, setTituloMostrar] = useState(titulo)
  const queCambiar = (resAPI === undefined) ? [fechas, region, zona, tienda, canal, depto, subDepto, mesRFM, anioRFM] : [resAPI]

  useEffect(() => {
    setTituloMostrar(titulo)
  }, [titulo])
  useEffect(async () => {
    let numero_tmp = 3.1416
    let hayResultados = 'no'
    let tituloMod_tmp = ''
    if (resAPI !== undefined) {
      if (resAPI !== 'cargando') {
        numero_tmp = resAPI.res[titulo_enviar]
        hayResultados = resAPI.hayResultados
      }
    } else {
      dispatchLoader({tipo: 'llamarAPI'})
      const res = await axios({
        method: 'post',
        url: `${CustomUrls.ApiUrl()}tarjetas/${seccion}?titulo=${titulo_enviar}`,
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
      numero_tmp = res.data.res
      hayResultados = res.data.hayResultados
      tituloMod_tmp = res.data.tituloMod
      dispatchLoader({tipo: 'recibirDeAPI'})
    }
    if (hayResultados === 'si') {
      if (numero_tmp !== '--') {
        if (formato === 'moneda') {
          const formatoMoneda = new Intl.NumberFormat('es-MX', {
            style: 'currency',
            currency: 'MXN'
          })
          numero_tmp = formatoMoneda.format(numero_tmp)
        } else if (formato === 'porcentaje') {
          const formatoPorcentaje = new Intl.NumberFormat('es-MX', {
            style: 'percent',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
          })
          numero_tmp = formatoPorcentaje.format(numero_tmp)
        } else if (formato === 'entero') {
          const formatoEntero = new Intl.NumberFormat('es-MX', {
            maximumFractionDigits: 0
          })
          numero_tmp = formatoEntero.format(numero_tmp)
        }
      }
      if (tituloMod_tmp !== undefined && tituloMod_tmp !== '') {
        // console.log(`tituloMod no está definido`)
        setTituloMostrar(tituloMod_tmp)
      } else {
        // console.log(`tituloMod sí está definido: ${tituloMod_tmp}`)
      }
      setNumero(numero_tmp)
    } else {
      setNumero("Sin Resultados")
      // console.log(JSON.stringify(numero_tmp))
    }
    // console.log(`Query ${titulo}:\n${JSON.stringify(res.data.pipeline)}`)
  }, queCambiar)

  return (
    <Card className='text-center'>
      <CardBody className={className}>
        {estadoLoader.contador === 0 && resAPI !== 'cargando' && <>
          <div className={`avatar p-50 m-0 mb-1 bg-light-primary`}>
            <div className='avatar-content'>{icono}</div>
          </div>
          <h3 className={`font-weight-bolder${(colorPositivo) ? ((parseFloat(numero) < 0) ? ' texto-rojo' : ' texto-verde') : ''}`}>{(colorPositivo) ? ((parseFloat(numero) < 0) ? '🠗' : '🠕') : ''}{ numero }</h3>
          <p className='card-text line-ellipsis'>{tituloMostrar}</p>
        </>}
        {(estadoLoader.contador !== 0 || resAPI === 'cargando') && <LoadingGif />}
      </CardBody>
    </Card>
  )
}

export default Tarjeta

// ** PropTypes
// Tarjeta.propTypes = {
//   icono: PropTypes.element.isRequired,
//   idComponente: PropTypes.string.isRequired,
//   titulo: PropTypes.string.isRequired,
//   formato: PropTypes.string.isRequired,
//   className: PropTypes.string
// }
