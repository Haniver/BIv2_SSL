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
import fechas_srv from '../../services/fechas_srv'
import { procesarSerie } from '../../services/funcionesAdicionales'
require('highcharts/modules/data')(Highcharts)
require('highcharts/modules/exporting')(Highcharts)
require('highcharts/modules/export-data')(Highcharts)

const EjesMultiplesConEscala = ({ titulo, yLabel, seccion, formato, fechas, region, zona, tienda, proveedor, categoria, tipoEntrega, tituloAPI, canal, mes, depto, subDepto, agrupador, periodo, nps, anioRFM, mesRFM, anio }) => {
    const [hayError, setHayError] = useState(false)
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
          url: `${CustomUrls.ApiUrl()}ejesMultiples/${seccion}?titulo=${titulo_enviar}`,
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
            mesRFM,
            anio
          }
        })
        dispatchLoader({tipo: 'recibirDeAPI'})
        let formato_columnas_tmp = 'entero'
        if (res.data.hayResultados === 'error') {
            setHayError(true)
        } else if (res.data.hayResultados === 'si') {
        setHayError(false)
            const series_tmp = []
            const yAxis_tmp = []
            res.data.series.forEach(elemento => {
                const yAxis_num = (elemento.type === 'column') ? 0 : 1
                // console.log(`yAxis_num = ${yAxis_num}`)
                if (elemento.type === 'column') {
                    formato_columnas_tmp = elemento.formato_tooltip
                }
                series_tmp.push({
                    name: elemento.name,
                    data: procesarSerie(elemento.data, elemento.formato_tooltip),
                    type: elemento.type,
                    yAxis: yAxis_num,
                    color: colors[elemento.color].main,
                    tooltip: {
                        pointFormatter () {
                                let valueDecimals = 2
                                let valuePrefix = ''
                                let valueSuffix = ''
                                if (elemento.formato_tooltip === 'moneda') {
                                    valuePrefix = '$'
                                } else if (elemento.formato_tooltip === 'entero') {
                                    valueDecimals = 0
                                } else if (elemento.formato_tooltip === 'porcentaje') {
                                    valueSuffix = '%'
                                }
                                const punto = this.options.y
                            return `${this.series.name}: <b>${valuePrefix}${Highcharts.numberFormat(punto, valueDecimals, '.', ',')}${valueSuffix}</b>`
                        }
                    }
                })
            })
            setCategories(res.data.categories)
            setSeries(series_tmp)
            setFormato_columnas(formato_columnas_tmp)
        } else {
            // console.log("No hay resultados")
            // setYAxis([])
            setCategories([])
            setSeries([])
            setFormato_columnas(formato_columnas_tmp)
        }
        // console.log(`Pipeline de ${titulo}: ${JSON.stringify(res.data.pipeline)}`)
      }, [fechas, region, zona, tienda, proveedor, categoria, tipoEntrega, depto, subDepto, canal, agrupador, periodo, nps, anioRFM, mesRFM, anio, mes])

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
            yAxis: [{ visible: false }, { visible: true, title: { text: yLabel } }],
            // yAxis: {
            //     title: {
            //         text: 'yLabel'
            //     },
            //     visible: true
            // },
            // yAxis: [
            //     {visible: true}, 
            //     {visible: true}
            // ],
            series,
            plotOptions: {
                column: {
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
                                return `${Highcharts.numberFormat(this.point.y, 2, '.', ',')}%`
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
                {hayError && <p classname='texto-rojo'>{`Error en la carga del componente "${tituloEnviar}" el ${fechas_srv.fechaYHoraActual()}`}</p>}
                {!hayError && estadoLoader.contador === 0 && <>
                    <HighchartsReact
                        highcharts={Highcharts}
                        options={options}
                        // ref={chartComponent}
                    />
                    {/* <button onClick={chartComponent.exportChart()}>Exportar</button> */}
                </>}
                {!hayError && estadoLoader.contador !== 0 && <LoadingGif />}
            </CardBody>
        </Card>
    )
}

export default EjesMultiplesConEscala