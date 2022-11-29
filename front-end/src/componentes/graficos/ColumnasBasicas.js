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

const ColumnasBasicas = ({ titulo, yLabel, seccion, formato, fechas, region, zona, tienda, proveedor, categoria, tipoEntrega, tituloAPI, periodo, agrupador, anioRFM, mesRFM }) => {
    const [hayError, setHayError] = useState(false)
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
        // console.log(`Periodo desde ColumnasBasicas = ${periodo}`)
        const tituloEnviar = (tituloAPI) ? tituloAPI : titulo // Como la API usa el título de la gráfica para regresar su valor, había un problema cuando ese título es variable, como cuando incluye la fecha actual. Entonces, si desde la vista le mandas el prop tituloAPI, es ese el que se usa para la API. Si lo omites, se usa la variable titulo como estaba pensado originalmente
        const res = await axios({
          method: 'post',
          url: `${CustomUrls.ApiUrl()}columnasBasicas/${seccion}?titulo=${tituloEnviar}`,
          headers: authHeader(),
          data: {
            fechas,            
            categoria,
            tipoEntrega,
            region,
            zona,
            tienda,
            proveedor,
            periodo,
            agrupador,
            anioRFM,
            mesRFM
          }
        })
        dispatchLoader({tipo: 'recibirDeAPI'})
        if (res.data.hayResultados === 'error') {
            setHayError(true)
        } else if (res.data.hayResultados === 'si') {
        setHayError(false)
            const series_tmp = []
            setCategorias(res.data.categorias)
            res.data.series.forEach(elemento => {
                series_tmp.push({
                    name: elemento.name,
                    data: procesarSerie(elemento.data, formato),
                    color: colors[elemento.color].main
                })
            })
            // console.log(`Data desde Columnas Básicas para ${titulo}:`)
            // console.log(series_tmp)
            setSeries(series_tmp)
            // console.log(JSON.stringify(res.data.pipeline))
        } else {
            setCategorias([])
            setSeries([])
        }
      }, [fechas, region, zona, tienda, proveedor, categoria, tipoEntrega, periodo, agrupador, anioRFM, mesRFM])
    
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
            labels:{
                formatter(tooltip) {
                    if (formato === 'moneda') {
                        return `$${Highcharts.numberFormat(this.value, 2, '.', ',')}`
                    } else if (formato === 'entero') {
                        return `${Highcharts.numberFormat(this.value, 0, '.', ',')}`
                    } else if (formato === 'porcentaje') {
                        return `${Highcharts.numberFormat(this.value, 0, '.', ',')}%`
                    }
                }
            }
        },
        plotOptions: {
            column: {
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
                            return `${Highcharts.numberFormat(this.point.y, 2, '.', ',')}%`
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
                    return `${this.series.name}: $${Highcharts.numberFormat(this.point.y, 2, '.', ',')}`
                } else if (formato === 'entero') {
                    return `${this.series.name}: ${Highcharts.numberFormat(this.point.y, 0, '.', ',')}`
                } else if (formato === 'porcentaje') {
                    return `${this.series.name}: ${Highcharts.numberFormat(this.point.y, 2, '.', ',')}%`
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

export default ColumnasBasicas