import { useState, useEffect, useContext, useReducer } from 'react'
import Highcharts from 'highcharts'
import HighchartsReact from 'highcharts-react-official'
import authHeader from '../../services/auth.header'
import axios from 'axios'
import CustomUrls from '../../services/customUrls'
import { ThemeColors } from '@src/utility/context/ThemeColors'
import { useSkin } from '@hooks/useSkin'
import { Card, CardBody } from 'reactstrap'
import drilldown from 'highcharts/modules/drilldown'
import LoadingGif from '../auxiliares/LoadingGif'
require('highcharts/modules/data')(Highcharts)
require('highcharts/modules/exporting')(Highcharts)
require('highcharts/modules/export-data')(Highcharts)

const ColumnasApiladas = ({ titulo, yLabel, seccion, formato, fechas, region, zona, tienda, proveedor, categoria, tipoEntrega, agrupador, periodo, tituloAPI }) => {
    const titulo_enviar = (tituloAPI !== undefined) ? tituloAPI : titulo
    const [series, setSeries] = useState([])
    const [categorias, setCategorias] = useState([])
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


    //Skins
    const [skin, setSkin] = useSkin()
    const colorTextoDark = '#CDCCCF'
    const colorTextoLight = '#272F44'
    const colorFondoDark = '#272F44'
    const colorFondoLight = 'white'
    // Esto es lo que tienes que cambiar manualmente para los colores del skin
    const [colorFondo, setColorFondo] = useState(colorFondoLight)
    const [colorTexto, setColorTexto] = useState(colorTextoLight)
    const { colors } = useContext(ThemeColors)
    
    drilldown(Highcharts)

    useEffect(() => {
        // Aquí también cambiar los colores dependiendo del skin, según líneas 18-19
        if (skin === 'dark') {
            setColorFondo(colorFondoDark)
            setColorTexto(colorTextoDark)
        } else {
            setColorFondo(colorFondoLight)
            setColorTexto(colorTextoLight)
        }
    }, [skin])

    useEffect(async () => {
        dispatchLoader({tipo: 'llamarAPI'})
        const res = await axios({
          method: 'post',
          url: `${CustomUrls.ApiUrl()}columnasApiladas/${seccion}?titulo=${titulo_enviar}`,
          headers: authHeader(),
          data: {
            fechas,            
            categoria,
            tipoEntrega,
            region,
            zona,
            tienda,
            proveedor, 
            agrupador, 
            periodo
          }
        })
        dispatchLoader({tipo: 'recibirDeAPI'})
        if (res.data.hayResultados === 'si') {
            const series_tmp = []
            setCategorias(res.data.categorias)
            console.log(`pipeline ${titulo}: ${JSON.stringify(res.data.pipeline)}`)
            res.data.series.forEach(elemento => {
                series_tmp.push({
                    name: elemento.name,
                    data: elemento.data,
                    color: colors[elemento.color].main
                })
            })
            setSeries(series_tmp)
            console.log('series:')
            console.log(series_tmp)
        } else {
            setCategorias([])
            setSeries([])
        }
      }, [fechas, region, zona, tienda, proveedor, categoria, tipoEntrega, agrupador, periodo])
    
    const options = {
        chart: {
            type: 'column',
            backgroundColor: colorFondo
        },
        title: {
            text: titulo,
            style: {
                color: colorTexto
            }
        },
        xAxis: {
            categories: categorias,
            labels: {
                style: {
                    fontWeight: 'bold',
                    color: colorTexto
                }
            }
        },
        yAxis: {
            min: 0,
            title: {
                text: yLabel
            },
            stackLabels: {
                enabled: true,
                style: {
                    fontWeight: 'bold',
                    color: colorTexto
                },
                formatter(tooltip) {
                    if (formato === 'moneda') {
                        return `$${Highcharts.numberFormat(this.total, 2, '.', ',')}`
                    } else if (formato === 'entero') {
                        return `${Highcharts.numberFormat(this.total, 0, '.', ',')}`
                    } else if (formato === 'porcentaje') {
                        return `${Highcharts.numberFormat(this.total * 100, 2, '.', ',')}%`
                    }
                }
            },
            labels:{
                formatter(tooltip) {
                    if (formato === 'moneda') {
                        return `$${Highcharts.numberFormat(this.value, 2, '.', ',')}`
                    } else if (formato === 'entero') {
                        return `${Highcharts.numberFormat(this.value, 0, '.', ',')}`
                    } else if (formato === 'porcentaje') {
                        return `${Highcharts.numberFormat(this.value * 100, 2, '.', ',')}%`
                    }
                }
            }
        },
        plotOptions: {
            column: {
                stacking: 'normal',
                dataLabels: {
                    enabled: true
                }
            },
            series: {
                dataLabels: {
                    enabled: true,
                    // format: '${point.y:,.2f}',
                    formatter(tooltip) {
                        if (formato === 'moneda') {
                            return `$${Highcharts.numberFormat(this.point.y, 2, '.', ',')}`
                        } else if (formato === 'entero') {
                            return `${Highcharts.numberFormat(this.point.y, 0, '.', ',')}`
                        } else if (formato === 'porcentaje') {
                            return `${Highcharts.numberFormat(this.point.y * 100, 2, '.', ',')}%`
                        }
                    },
                    color: colorTexto,
                    textOutline: colorTexto
                    // style: {
                    //     fontWeight: 'bold',
                    //     color: colorTexto,
                    //     textOutline: colorFondo
                    // }
                }
            }
        },
        tooltip: {
            headerFormat: '<b>{point.x}</b><br/>',
            formatter(tooltip) {
                if (formato === 'moneda') {
                    return `${this.series.name}: $${Highcharts.numberFormat(this.point.y, 2, '.', ',')}<br/>Total: $${Highcharts.numberFormat(this.point.stackTotal, 2, '.', ',')}`
                } else if (formato === 'entero') {
                    return `${this.series.name}: ${Highcharts.numberFormat(this.point.y, 0, '.', ',')}<br/>Total: ${Highcharts.numberFormat(this.point.stackTotal, 0, '.', ',')}`
                } else if (formato === 'porcentaje') {
                    return `${this.series.name}: ${Highcharts.numberFormat(this.point.y * 100, 2, '.', ',')}%<br/>Total: ${Highcharts.numberFormat(this.point.stackTotal * 100, 2, '.', ',')}%`
                }
        }
        },
        legend: {
            itemStyle: {
                color: colorTexto,
                fontWeight: 'bold'
            }
        },
        series,
        credits: {
            enabled: false
        }
    }

    return (
        <Card>
            <CardBody>
                {estadoLoader.contador === 0 && <>
                    <HighchartsReact
                        highcharts={Highcharts}
                        options={options}
                        // ref={chartComponent}
                    />
                    {/* <button onClick={chartComponent.exportChart()}>Exportar</button> */}
                </>}
                {estadoLoader.contador !== 0 && <LoadingGif />}
            </CardBody>
        </Card>
    )
}

export default ColumnasApiladas