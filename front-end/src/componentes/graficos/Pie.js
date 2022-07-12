import { useState, useEffect, useContext, useReducer } from 'react'
import Highcharts from 'highcharts'
import HighchartsReact from 'highcharts-react-official'
import authHeader from '../../services/auth.header'
import axios from 'axios'
import CustomUrls from '../../services/customUrls'
import { ThemeColors } from '@src/utility/context/ThemeColors'
import { useSkin } from '@hooks/useSkin'
import { Card, CardBody } from 'reactstrap'
import LoadingGif from '../auxiliares/LoadingGif'
require('highcharts/modules/data')(Highcharts)
require('highcharts/modules/exporting')(Highcharts)
require('highcharts/modules/export-data')(Highcharts)

const Pie = ({ titulo, seccion, formato, fechas, region, zona, tienda, tipoEntrega, origen, coloresPedidosPendientes, categoria }) => {
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
          url: `${CustomUrls.ApiUrl()}pie/${seccion}?titulo=${titulo}`,
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
        if (res.data.hayResultados === 'si') {
            let total_tmp = 0
            datos_tmp.forEach(dato => {
                total_tmp += dato.y
            })
            total_tmp = total_tmp.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",")
            setDatos(datos_tmp)
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
            text: titulo,
            style: {
                color: colorTexto
            }
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
        },
        // Label de Total personalizado
        chart: {
            events: {
              render() {
                removeLabel(this)
                addLabel(this)
              }
            }
          }
    }
    return (
        <Card>
            <CardBody>
                {estadoLoader.contador === 0 && <HighchartsReact
                    highcharts={Highcharts}
                    options={options}
                />}
                {estadoLoader.contador !== 0 && <LoadingGif />}
            </CardBody>
        </Card>
    )
}

export default Pie