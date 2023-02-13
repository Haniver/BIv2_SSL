import authHeader from '../../services/auth.header'
import axios from 'axios'
import { useState, useEffect, useContext, useReducer } from 'react'
import CustomUrls from '../../services/customUrls'
import LoadingGif from '../auxiliares/LoadingGif'
import fechas_srv from '../../services/fechas_srv'
import Highcharts, { setOptions } from 'highcharts'
import HighchartsReact from 'highcharts-react-official'
import { ThemeColors } from '@src/utility/context/ThemeColors'
import { useSkin } from '@hooks/useSkin'
require('highcharts/modules/data')(Highcharts)
require('highcharts/modules/exporting')(Highcharts)
require('highcharts/modules/export-data')(Highcharts)

// ** Custom Components
import Avatar from '@components/avatar'

// ** Reactstrap Imports
import { Card, CardHeader, CardTitle, CardBody, CardText, Row, Col } from 'reactstrap'

const IndicadoresEnBarras = ({ cols, icono, titulo, tituloAPI, seccion, className, formato, fechas, region, zona, tienda, proveedor, depto, subDepto, canal, anioRFM, mesRFM, resAPI, colorPositivo }) => {
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
  const [skin, setSkin] = useSkin()
  const colorTextoDark = '#CDCCCF'
  const colorTextoLight = '#272F44'
  const colorFondoDark = '#272F44'
  const colorFondoLight = 'white'
  // Esto es lo que tienes que cambiar manualmente para los colores del skin
  const [colorFondo, setColorFondo] = useState(colorFondoLight)
  const [colorTexto, setColorTexto] = useState(colorTextoLight)
  const { colors } = useContext(ThemeColors)

  const [bloques, setBloques] = useState([{highcharts: Highcharts, options: {}, laterales: []}])
  const updateBloques = async (opcionesFila, lateralesTmp) => {
    return new Promise((resolve, reject) => {
      setBloques(prevBloques => [
        ...prevBloques,
        {
          highcharts: Highcharts,
          options: opcionesFila,
          laterales: lateralesTmp
        }
      ])
      resolve()
    })
  }
  const fetchData = async () => {
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
        url: `${CustomUrls.ApiUrl()}indicadoresEnBarras/${seccion}?titulo=${tituloEnviar}`,
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
      resultado_tmp = res.data.res
      dispatchLoader({tipo: 'recibirDeAPI'})
      // let visitado  = false
      // Iteramos sobre el resultado y obtenemos cada bloque de indicadores:
      let contador = 1
      resultado_tmp.forEach(async fila => {
        // Empezamos con el gráfico de barras
        contador += 1
        const seriesData_fila = []
        let contador2 = 1
        fila.barras.forEach(indicador => {
          contador2 += 1
          const color = (['primary', 'secondary', 'success', 'info', 'warning', 'danger', 'light', 'dark'].includes(indicador.color)) ? colors[indicador.color].main : indicador.color
          seriesData_fila.push({name: indicador.titulo, y: indicador.valor, color})
        })  
        const opcionesFila = {
          chart: {
              type: 'bar',
              height: 150
          },
          title: {
              text: fila.titulo,
              align: 'left',
              style: {
                fontFamily: '"Noto Sans", Helvetica, Arial, serif',
                fontSize: '14px'
              }
          },
          xAxis: {
              type: 'category',
              gridLineWidth: 0
          },
          yAxis: {
            min: 0,
            title: "",
            gridLineWidth: 0,
            labels: {
              enabled: false
            }
          },
          plotOptions: {
            bar: {
              dataLabels: {
                enabled: true,
                formatter(tooltip) {
                    if (fila.formatoBarras === 'moneda') {
                        return `$${Highcharts.numberFormat(this.point.y, 2, '.', ',')}`
                    } else if (fila.formatoBarras === 'entero') {
                        return `${Highcharts.numberFormat(this.point.y, 0, '.', ',')}`
                    } else if (fila.formatoBarras === 'porcentaje') {
                        return `${Highcharts.numberFormat(this.point.y, 2, '.', ',')}%`
                    }
                },
                color: colorTexto,
                textOutline: colorTexto
              }
            }
          },
          tooltip: {
            formatter() {
              if (fila.formatoBarras === 'moneda') {
                return `<b>${this.point.name}</b>: $${Highcharts.numberFormat(this.point.y, 2, '.', ',')}`
              } else if (fila.formatoBarras === 'entero') {
                  return `<b>${this.point.name}</b>: ${Highcharts.numberFormat(this.point.y, 0, '.', ',')}`
              } else if (fila.formatoBarras === 'porcentaje') {
                  return `<b>${this.point.name}</b>: ${Highcharts.numberFormat(this.point.y, 2, '.', ',')}%`
              }
              return `<b>${this.point.name}</b>: ${this.point.y}`
            }
          },
          legend: {
              enabled: false
          },
          series: [
            {
              data: seriesData_fila
            }
          ],
          credits: {
            enabled: false
          }
        }
        
        // Seguimos con los indicadores laterales (los que vienen sueltos)
        const lateralesTmp = []
        fila.laterales.forEach(indicador => {
          let formato = ''
          if (indicador.formato === 'moneda') {
            formato = new Intl.NumberFormat('es-MX', {
              style: 'currency',
              currency: 'MXN'
            })
          } else if (indicador.formato === 'porcentaje') {
            formato = new Intl.NumberFormat('es-MX', {
              style: 'percent',
              minimumFractionDigits: 2,
              maximumFractionDigits: 2
            })
          } else {
            formato = new Intl.NumberFormat('es-MX', {
              maximumFractionDigits: 0
            })
          }
          lateralesTmp.push({
            valor: formato.format(indicador.valor),
            color: ((indicador.valor) < 0) ? colors['danger'].main : colors['dark'].main,
            titulo: indicador.titulo
          })
        })
        
        await updateBloques(opcionesFila, lateralesTmp)
      })
    }
  }
  useEffect(() => {
    fetchData()
  }, [fechas, region, zona, tienda, canal, depto, subDepto, mesRFM, anioRFM])

  return (
    <Card>
      <CardBody className={className}>
      <CardTitle className='centrado'>{titulo}</CardTitle>
      {estadoLoader.contador === 0 && resAPI !== 'cargando' && bloques.filter(bloque => Object.keys(bloque.options).length > 0).map((bloque, index) => (
        <Row key={index} style={{display: 'flex', alignItems: 'center'}}>
          <Col sm='12' lg={String(12 - (bloque.laterales.length * 2))}>
            <HighchartsReact
              highcharts={bloque.highcharts}
              options={bloque.options}
            />
          </Col>
          {bloque.laterales.map((lateral, index2) => (
            <Col sm='12' lg='2' className='centrado' key={(index * 100) + index2}>
            <h1 style={{ color: lateral.color, fontWeight: 'bold' }}>{lateral.valor}</h1>
              <p>{lateral.titulo}</p>
            </Col>
          ))}
        </Row>
      ))}
      {/* {(estadoLoader.contador !== 0 || resAPI === 'cargando' || bloques[0].laterales.length > 0) && <LoadingGif />} */}
      {(estadoLoader.contador !== 0 || resAPI === 'cargando') && <LoadingGif />}
      </CardBody>
    </Card>
  )
}

export default IndicadoresEnBarras
