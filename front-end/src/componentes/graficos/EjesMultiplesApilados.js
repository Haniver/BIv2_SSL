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

const EjesMultiplesApilados = ({ titulo, seccion, fechas, tituloAPI }) => {
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
    const [yAxis, setYAxis] = useState([])
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
          url: `${CustomUrls.ApiUrl()}ejesMultiplesApilados/${seccion}?titulo=${titulo_enviar}`,
          headers: authHeader(),
          data: {
            fechas
          }
        })
        dispatchLoader({tipo: 'recibirDeAPI'})
        let formato_columnas_tmp = 'entero'
        if (res.data.hayResultados === 'si') {
            const series_tmp = []
            res.data.series.forEach(elemento => {
                if (elemento.type === 'column') {
                    formato_columnas_tmp = elemento.formato_tooltip
                }
                series_tmp.push({
                    name: elemento.name,
                    data: elemento.data,
                    type: elemento.type,
                    yAxis: elemento.yAxis,
                    color: colors[elemento.color].main,
                    tooltip: {
                        pointFormatter () {
                                let valueDecimals = 2
                                let valuePrefix = ''
                                let valueSuffix = ''
                                let multiplicador = 1
                                if (elemento.formato_tooltip === 'moneda') {
                                    valuePrefix = '$'
                                } else if (elemento.formato_tooltip === 'entero') {
                                    valueDecimals = 0
                                } else if (elemento.formato_tooltip === 'porcentaje') {
                                    valueSuffix = '%'
                                    multiplicador = 100
                                }
                                const punto = multiplicador * this.options.y
                            return `${this.series.name}: <b>${valuePrefix}${Highcharts.numberFormat(punto, valueDecimals, '.', ',')}${valueSuffix}</b>`
                        }
                    }
                })
                // El requerimiento fue no usar labels y títulos para el eje de las Y, pero si en un futuro lo quieres hacer, tiene que cumplir con el formato de https://jsfiddle.net/gh/get/library/pure/highcharts/highcharts/tree/master/samples/highcharts/demo/combo-multi-axes
                // yAxis_tmp.push({
                //     visible: false
                // })
            })
            const yAxis_tmp = []
            res.data.yAxis.forEach(elemento => {
                let formato = ''
                if (elemento.formato === 'entero') {
                    formato = '{value:,.0f}'
                } else if (elemento.formato === 'porcentaje') {
                    formato = '{value:,.2f}%'
                } else if (elemento.formato === 'moneda') {
                    formato = '${value:,.2f}'
                }
                yAxis_tmp.push({
                    labels: {
                        format: formato,
                        style: {
                            color: colors[elemento.color].main
                        }
                    },
                    title: {
                        text: elemento.titulo,
                        style: {
                            color: colors[elemento.color].main
                        }
                    },
                    opposite: elemento.opposite
            
                })
            })
            // console.log("YAxis desde EjesMultiples:")
            // console.log(yAxis_tmp)
            // console.log("Categories desde EjesMultiples:")
            // console.log(res.data.categories)
            // console.log("Series desde EjesMultiples:")
            // console.log(series_tmp)
            setYAxis(yAxis_tmp)
            setCategories(res.data.categories)
            setSeries(series_tmp)
            setFormato_columnas(formato_columnas_tmp)
        } else {
            // console.log("No hay resultados")
            setYAxis([])
            setCategories([])
            setSeries([])
            setFormato_columnas(formato_columnas_tmp)
        }
        // console.log(`Pipeline de ${titulo}: ${JSON.stringify(res.data.pipeline)}`)
      }, [fechas])

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
            yAxis,
            series,
            plotOptions: {
                column: {
                    stacking: 'normal',
                    dataLabels: {
                        enabled: true,
                        crop: false,
                        overflow: 'none',
                        formatter(tooltip) { // Esto es para los números que salen encima de las barras
                            // console.log(`this:`)
                            if (formato_columnas === 'moneda') {
                                return `$${Highcharts.numberFormat(this.point.y, 2, '.', ',')}`
                            } else if (formato_columnas === 'entero') {
                                return `${Highcharts.numberFormat(this.point.y, 0, '.', ',')}`
                            } else if (formato_columnas === 'porcentaje') {
                                return `${Highcharts.numberFormat(this.point.y * 100, 2, '.', ',')}%`
                            } else {
                                return 'nada nada no no no'
                            }
                        }    
                    }
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

export default EjesMultiplesApilados