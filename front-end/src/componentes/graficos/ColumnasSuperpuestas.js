// Todavía falta limpiar esto, porque los useState tienen todo el ejemplo como valor inicial
// Además, hay un options2 que hay que quitar
// Además hay muchas cosas comentadas

// Aguas, porque hay que mandar los porcentajes multiplicados por 100 desde la API, porque no pude cambiarlos aquí.

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

const ColumnasSuperpuestas = ({ titulo, yLabel, seccion, formato, fechas, region, zona, tienda, proveedor, categoria, tipoEntrega, tituloAPI, canal, mes, depto, subDepto, agrupador, periodo, nps, anioRFM, mesRFM }) => {
    const titulo_enviar = (tituloAPI) ? tituloAPI : titulo // Como la API usa el título de la gráfica para regresar su valor, había un problema cuando ese título es variable, como cuando incluye la fecha actual. Entonces, si desde la vista le mandas el prop tituloAPI, es ese el que se usa para la API. Si lo omites, se usa la variable titulo como estaba pensado originalmente
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
    const [series, setSeries] = useState([])
    const [options, setOptions] = useState({
        chart: {
            zoomType: 'xy'
        },
        title: {
            text: 'Espera a que carguen los datos'
        },
        xAxis: [
            {
                categories: []
            }
        ],
        yAxis: [],
        series: [],
        credits: {
            enabled: false
        }   
    })
    const [categories, setCategories] = useState([])
    const [formato_columnas, setFormato_columnas] = useState()
    // const [yLabelFormat1, setYLabelFormat1] = useState({formato:'{value}', color: '#000', texto: ''})
    // const [yLabelFormat2, setYLabelFormat2] = useState({formato:'{value}', color: '#000', texto: ''})

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
    
    Highcharts.setOptions({
        lang: {
            thousandsSep: ','
        }
    })

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
          url: `${CustomUrls.ApiUrl()}columnasSuperpuestas/${seccion}?titulo=${titulo_enviar}`,
          headers: authHeader(),
          data: {
            fechas,            
            categoria,
            tipoEntrega,
            region,
            zona,
            tienda,
            proveedor,
            canal,
            mes,
            depto, 
            subDepto,
            agrupador,
            periodo,
            nps,
            anioRFM,
            mesRFM
          }
        })
        dispatchLoader({tipo: 'recibirDeAPI'})
        let formato_columnas_tmp = 'entero'
        if (res.data.hayResultados === 'si') {
            // const series_tmp = []
            const yAxis_tmp = []
            // res.data.series.forEach(elemento => {
                const elemento = res.data.series
                // const yAxis_num = (elemento.type === 'column') ? 0 : 1
                // if (elemento.type === 'column') {
                    formato_columnas_tmp = elemento.formato_tooltip
                // }
                // series_tmp.push({
            let valueDecimalsTexto1 = '.2f'
            let valueDecimalsTexto2 = '.2f'
            let valuePrefix1 = ''
            let valuePrefix2 = ''
            let valueSuffix1 = ''
            let valueSuffix2 = ''
            if (elemento[0].formato === 'moneda') {
                valuePrefix1 = '$'
            } else if (elemento[0].formato === 'entero') {
                valueDecimalsTexto1 = '.0f'
            } else if (elemento[0].formato === 'porcentaje') {
                valueSuffix1 = '%'
                multiplicador1 = 100
            }
            if (elemento[1].formato === 'moneda') {
                valuePrefix2 = '$'
            } else if (elemento[1].formato === 'entero') {
                valueDecimalsTexto2 = '.0f'
            } else if (elemento[1].formato === 'porcentaje') {
                valueSuffix2 = '%'
                multiplicador2 = 100
            }
            const series_tmp = [
                   {
                    name: elemento[0].name,
                    data: elemento[0].data,
                    // type: elemento.type,
                    type: 'column',
                    yAxis: 1,
                    color: colors[elemento[0].color].main,
                    dataLabels: {
                        enabled: true,
                        crop: false,
                        overflow: 'none',
                        format: `${valuePrefix1}{point.y:,${valueDecimalsTexto1}}${valueSuffix1}`
                    },
                    tooltip: {
                        pointFormatter () {
                            let valueDecimals = 2
                            let valueDecimalsTexto = '.2f'
                            let valuePrefix = ''
                            let valueSuffix = ''
                            let multiplicador = 1
                            if (elemento[0].formato === 'moneda') {
                                valuePrefix = '$'
                            } else if (elemento[0].formato === 'entero') {
                                valueDecimals = 0
                                valueDecimalsTexto = '.0f'
                            } else if (elemento[0].formato === 'porcentaje') {
                                valueSuffix = '%'
                                multiplicador = 100
                            }
                            const punto = multiplicador * this.options.y
                            return `${this.series.name}: <b>${valuePrefix}${Highcharts.numberFormat(punto, valueDecimals, '.', ',')}${valueSuffix}</b><br />`
                        }
                    },
                    pointPadding: 0.3
                }, {
                    name: elemento[1].name,
                    data: elemento[1].data,
                    // type: elemento.type,
                    type: 'column',
                    // yAxis: 1,
                    color: colors[elemento[1].color].main,
                    // dataLabels: {
                    //     enabled: true,
                    //     crop: false,
                    //     overflow: 'none',
                    //     format: {
                    //         pointFormatter () {
                    //             let valueDecimals = 2
                    //             let valueDecimalsTexto = '.2f'
                    //             let valuePrefix = ''
                    //             let valueSuffix = ''
                    //             let multiplicador = 1
                    //             if (elemento[1].formato === 'moneda') {
                    //                 valuePrefix = '$'
                    //             } else if (elemento[1].formato === 'entero') {
                    //                 valueDecimals = 0
                    //                 valueDecimalsTexto = '.0f'
                    //             } else if (elemento[1].formato === 'porcentaje') {
                    //                 valueSuffix = '%'
                    //                 multiplicador = 100
                    //             }
                    //             const punto = multiplicador * this.options.y
                    //             return `${valuePrefix}{point.y:${valueDecimalsTexto}}${valueSuffix}`
                    //         }
                    //     }
                    // },
                    dataLabels: {
                        enabled: true,
                        crop: false,
                        overflow: 'none',
                        format: `${valuePrefix2}{point.y:,${valueDecimalsTexto2}}${valueSuffix2}`
                    },
                    tooltip: {
                        pointFormatter () {
                                let valueDecimals = 2
                                let valuePrefix = ''
                                let valueSuffix = ''
                                let multiplicador = 1
                                if (elemento[1].formato === 'moneda') {
                                    valuePrefix = '$'
                                } else if (elemento[1].formato === 'entero') {
                                    valueDecimals = 0
                                } else if (elemento[1].formato === 'porcentaje') {
                                    valueSuffix = '%'
                                    multiplicador = 100
                                }
                                const punto = multiplicador * this.options.y
                            return `${this.series.name}: <b>${valuePrefix}${Highcharts.numberFormat(punto, valueDecimals, '.', ',')}${valueSuffix}</b>`
                        }
                    },
                    pointPadding: 0.4
                // })
                }
            ]
                // El requerimiento fue no usar labels y títulos para el eje de las Y, pero si en un futuro lo quieres hacer, tiene que cumplir con el formato de https://jsfiddle.net/gh/get/library/pure/highcharts/highcharts/tree/master/samples/highcharts/demo/combo-multi-axes
                // yAxis_tmp.push({
                //     visible: false
                // })
            // })
            // console.log("YAxis desde EjesMultiples:")
            // console.log(yAxis_tmp)
            // console.log("Categories desde EjesMultiples:")
            // console.log(res.data.categories)
            // console.log("Series desde EjesMultiples:")
            // console.log(series_tmp)
            // setYAxis(yAxis_tmp)
            setCategories(res.data.categories)
            // console.log('Data desde ColumnasSuperpuestas:')
            // console.log(series_tmp)
            setSeries(series_tmp)
            setFormato_columnas(formato_columnas_tmp)
            // const formato1 = (elemento[0].formato === 'moneda') ? '${value}' : '{value}'
            // setYLabelFormat1({formato: formato1, color: elemento[0].color, texto: elemento[0].name})
            // const formato2 = (elemento[1].formato === 'moneda') ? '${value}' : '{value}'
            // setYLabelFormat2({formato: formato2, color: elemento[1].color, texto: elemento[1].name})
        } else {
            // console.log("No hay resultados")
            // setYAxis([])
            setCategories([])
            setSeries([])
            setFormato_columnas(formato_columnas_tmp)
        }
        // console.log(`Pipeline de ${titulo}: ${JSON.stringify(res.data.pipeline)}`)
      }, [fechas, region, zona, tienda, proveedor, categoria, tipoEntrega, depto, subDepto, canal, agrupador, periodo, nps, anioRFM, mesRFM])

    useEffect(() => {
        const options = {
            chart: {
                zoomType: 'xy',
                backgroundColor: colorFondo
            },
            title: {
                text: titulo,
                style: {
                    color: colorTexto
                }
            },
            xAxis: [
                {
                    categories,
                    style: {
                        fontWeight: 'bold',
                        color: colorTexto
                    }
                }
            ],
        //     yAxis: [
        //         { // Primary yAxis
        //         labels: {
        //             format: yLabelFormat2.formato,
        //             style: {
        //                 color: yLabelFormat2.color
        //             }
        //         },
        //         title: {
        //             text: yLabelFormat2.texto,
        //             style: {
        //                 color: yLabelFormat2.color
        //             }
        //         }
        //     }, { // Secondary yAxis
        //         title: {
        //             text: yLabelFormat1.texto,
        //             style: {
        //                 color: yLabelFormat1.color
        //             }
        //         },
        //         labels: {
        //             format: yLabelFormat1.formato,
        //             style: {
        //                 color: yLabelFormat1.color
        //             }
        //         },
        //         opposite: true
        //     }
        // ],
            yAxis: [
                {visible: false}, 
                {visible: false}
            ],
            series,
            tooltip: {
                shared: true
            },
            plotOptions: {
                column: {
                    grouping: false,
                    shadow: false,
                    borderWidth: 0
                    // dataLabels: {
                    //     enabled: true,
                    //     crop: false,
                    //     overflow: 'none',
                    //     formatter(tooltip) { // Esto es para los números que salen encima de las barras
                    //         // console.log(`this:`)
                    //         if (formato_columnas === 'moneda') {
                    //             return `$${Highcharts.numberFormat(this.point.y, 2, '.', ',')}`
                    //         } else if (formato_columnas === 'entero') {
                    //             return `${Highcharts.numberFormat(this.point.y, 0, '.', ',')}`
                    //         } else if (formato_columnas === 'porcentaje') {
                    //             return `${Highcharts.numberFormat(this.point.y * 100, 2, '.', ',')}%`
                    //         } else {
                    //             return 'nada nada no no no'
                    //         }
                    //     }    
                    // }
                }
            },
            credits: {
                enabled: false
            }   
        }
        setOptions(options)
    }, [series, formato_columnas])

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

export default ColumnasSuperpuestas