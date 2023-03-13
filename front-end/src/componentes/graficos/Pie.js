import { useState, useEffect, useContext, useReducer } from 'react'
import Highcharts from 'highcharts'
import HighchartsReact from 'highcharts-react-official'
import authHeader from '../../services/auth.header'
import axios from 'axios'
import CustomUrls from '../../services/customUrls'
import { ThemeColors } from '@src/utility/context/ThemeColors'
import { useSkin } from '@hooks/useSkin'
import { Card, CardBody, CardTitle } from 'reactstrap'
import LoadingGif from '../auxiliares/LoadingGif'
import fechas_srv from '../../services/fechas_srv'
require('highcharts/modules/data')(Highcharts)
require('highcharts/modules/exporting')(Highcharts)
require('highcharts/modules/export-data')(Highcharts)

const Pie = ({ titulo, tituloAPI, seccion, formato, fechas, region, zona, tienda, tipoEntrega, origen, coloresPedidosPendientes, categoria, extenderDerecha, extenderIzquierda, ocultarTotal, totalDesdePadre, setTotalDesdePadre }) => {
    const tituloEnviar = (tituloAPI !== undefined) ? tituloAPI : titulo
    const [hayError, setHayError] = useState(false)
    const [datos, setDatos] = useState([{name: 'Sin Resultados', y: 0}])
    const [total, setTotal] = useState('')
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

    let claseCSS = ''
    if (extenderDerecha) {
        claseCSS = 'extenderDerecha'
    } else if (extenderIzquierda) {
        claseCSS = 'extenderIzquierda'
    }

    const [skin, setSkin] = useSkin()
    const colorTextoDark = '#CDCCCF'
    const colorTextoLight = '#272F44'
    const colorFondoDark = '#272F44'
    const colorFondoLight = 'white'
    const [colorFondo, setColorFondo] = useState(colorFondoDark)
    const [colorTexto, setColorTexto] = useState(colorTextoDark)
    const { colors } = useContext(ThemeColors)
    const colorDeRebanadas = (coloresPedidosPendientes) ? [colors.info.main, colors.dark.main, colors.warning.main, colors.primary.main, colors.danger.main] : [colors.secondary.main, colors.primary.main, colors.dark.main, colors.warning.main, colors.info.main, colors.danger.main]

    // Skins
    useEffect(() => {
        // console.log(`skin cambió a ${skin} desde Pie`)
    // Aquí también cambiar los colores dependiendo del skin, según líneas 18-19
        if (skin === 'dark') {
            // console.log('Skin es dark')
            setColorFondo(colorFondoDark)
            setColorTexto(colorTextoDark)
        } else {
            // console.log('Skin no es dark')
            setColorFondo(colorFondoLight)
            setColorTexto(colorTextoLight)
        }
    }, [skin])

    useEffect(async () => {
        dispatchLoader({tipo: 'llamarAPI'})
        const res = await axios({
          method: 'post',
          url: `${CustomUrls.ApiUrl()}pie/${seccion}?titulo=${tituloEnviar}`,
          headers: authHeader(),
          data: {
            fechas,            
            region,
            zona,
            tienda,
            tipoEntrega, 
            origen,
            categoria
          }
        })
        dispatchLoader({tipo: 'recibirDeAPI'})
        const datos_tmp = res.data.res
        if (res.data.hayResultados === 'error') {
            setHayError(true)
        } else if (res.data.hayResultados === 'si') {
        setHayError(false)
            let total_tmp = 0
            datos_tmp.forEach(dato => {
                total_tmp += dato.y
                if (dato.color !== undefined && ['primary', 'secondary', 'success', 'info', 'warning', 'danger', 'light', 'dark'].includes(dato.color)) {
                    dato.color = colors[dato.color].main
                }
            })
            total_tmp = total_tmp.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",")
            setDatos(datos_tmp)
            if (setTotalDesdePadre !== undefined) {
                // console.log(`total en Pie se va a poner en ${total_tmp} (dentro del if)`)
                // console.log('setTotalDesdePadre:')
                // console.log(setTotalDesdePadre)
                setTotalDesdePadre(total_tmp)
            }
            // console.log(`total en Pie se va a poner en ${total_tmp} (fuera del if)`)
            setTotal(total_tmp)
        } else {
          setDatos({name: 'Sin Resultados', y: 0})
        }
      }, [fechas, region, zona, tienda, tipoEntrega, origen, categoria])

    // Lo que sigue es para borrar y volver a crear el label de Total, según https://www.highcharts.com/forum/viewtopic.php?t=38132
    const objectIsEmpty = (obj) => {
        return Object.keys(obj).length === 0 && obj.constructor === Object
    }

    const addLabel = (chart) => {
        chart.myLabel = chart.renderer.label(`Total: ${total}`, 10, 100).css({
            fontSize: '1rem',
            color: '#272F44'
        }).add()
    }
    const removeLabel = (chart) => {
        if (chart.myLabel && !objectIsEmpty(chart.myLabel)) {
            chart.myLabel.destroy()
        }
    }
    const options = {
        chart: {
            type: 'pie',
            options3d: {
                enabled: false,
                alpha: 45,
                beta: 0
            },
            backgroundColor: colorFondo
        },
        title: {
            text: ''
        },
        xAxis: {
            labels: {
               style: {
                  color: colorTexto
               }
            }
        },
        yAxis: {
            labels: {
               style: {
                  color: colorTexto
               }
            }
        },
        accessibility: {
            point: {
                valuePrefix: '$'
            }
        },
        tooltip: {
            formatter(tooltip) {
                if (formato === 'moneda') {
                    return `${this.point.name}<br>Monto: $${Highcharts.numberFormat(this.point.y, 2, '.', ',')}`
                } else if (formato === 'entero') {
                    return `${this.point.name}<br>Cantidad: ${Highcharts.numberFormat(this.point.y, 0, '.', ',')}`
                } else if (formato === 'porcentaje') {
                    return `${this.point.name}<br>Porcentaje: ${100 * Highcharts.numberFormat(this.point.y, 4, '.', ',')}%`
                }
            },
            shared: true
        },
        plotOptions: {
            pie: {
                allowPointSelect: true,
                cursor: 'pointer',
                depth: 35,
                dataLabels: {
                    enabled: true,
                    formatter(dataLabels) {
                        if (formato === 'moneda') {
                            return `${this.point.name}<br>${Highcharts.numberFormat(this.point.percentage, 1, '.', ',')}%<br>$${Highcharts.numberFormat(this.point.y, 2, '.', ',')}`
                        } else if (formato === 'entero') {
                            return `${this.point.name}<br>${Highcharts.numberFormat(this.point.percentage, 1, '.', ',')}%<br>${Highcharts.numberFormat(this.point.y, 0, '.', ',')}`
                        } else if (formato === 'porcentaje') {
                            return `${this.point.name}<br>${Highcharts.numberFormat(100 * this.point.y, 2, '.', ',')}%`
                        }
                    }
                },
                colors: colorDeRebanadas
            },
            series: {
                dataLabels: {
                    enabled: true,
                    style: {
                        fontWeight: 'bold',
                        color: colorTexto,
                        textOutline: colorFondo
                    }
                }
            }    
        },
        series: [
            {
                type: 'pie',
                name: 'Monto',
                data: datos  
            }
        ],
        credits: {
            enabled: false
        }
    }
    // Label de Total personalizado
    if (!ocultarTotal) {
        options.chart = {
            events: {
              render() {
                removeLabel(this)
                addLabel(this)
              }
            }
        }
    }
    return (
        <Card className={claseCSS}>
            <CardBody>
                {hayError && <p classname='texto-rojo'>{`Error en la carga del componente "${tituloEnviar}" el ${fechas_srv.fechaYHoraActual()}`}</p>}
                {!hayError && estadoLoader.contador === 0 && <>
                <CardTitle className='centrado'>{titulo}</CardTitle>
                <HighchartsReact
                    highcharts={Highcharts}
                    options={options}
                />
                </>}
                {!hayError && estadoLoader.contador !== 0 && <LoadingGif />}
            </CardBody>
        </Card>
    )
}

export default Pie