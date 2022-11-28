// https://jsfiddle.net/BlackLabel/23qt8m5e/
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
import HC_more from 'highcharts/highcharts-more'
HC_more(Highcharts)
require('highcharts/modules/data')(Highcharts)
require('highcharts/modules/exporting')(Highcharts)
require('highcharts/modules/export-data')(Highcharts)

const Burbuja3D = ({ titulo, yLabel, seccion, formato, fechas, region, zona, tienda, proveedor, categoria, tipoEntrega, tituloAPI, periodo, agrupador, anioRFM, mesRFM }) => {
    const [hayError, setHayError] = useState(false)
    const [data, setData] = useState([])
    const [categoriesX, setCategoriesX] = useState([])
    const [categoriesY, setCategoriesY] = useState([])
    const [tituloX, setTituloX] = useState('')
    const [tituloY, setTituloY] = useState('')
    const { colors } = useContext(ThemeColors)
    const [colorBurbuja, setColorBurbuja] = useState('primary')
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

    const [options, setOptions] = useState({
        chart: {
            type: 'bubble',
            plotBorderWidth: 1,
            zoomType: 'xy'
        },
    
        title: {
            text: 'Espera a que carguen los datos'
        },
    
        xAxis: {
            gridLineWidth: 1,
            categories: [],
            title: {
                text: ''
            }
        },
    
        yAxis: {
            startOnTick: false,
            endOnTick: false,
            categories: [],
            title: {
                text: ''
            }
        },
    
        series: [
            {
                showInLegend: false,
                data,
                    marker: {
                    fillColor: {
                        radialGradient: { cx: 0.4, cy: 0.3, r: 0.7 },
                        stops: [
                            [0, 'rgba(255,255,255,0.5)'],
                            [1, '#FF0000']
                        ]
                    }
                }
            }
        ]
    })
    useEffect(() => {
        const options_tmp = {
            chart: {
                type: 'bubble',
                plotBorderWidth: 0,
                zoomType: 'xy'
            },
        
            title: {
                text: titulo
            },
        
            xAxis: {
                gridLineWidth: 0,
                categories: categoriesX,
                title: {
                    text: tituloX
                }
            },
        
            yAxis: {
                startOnTick: false,
                endOnTick: false,
                gridLineWidth: 0,
                categories: categoriesY,
                title: {
                    text: tituloY
                }
            },
            tooltip: {
                format: '{point.y:,.0f}%'
            },
            plotOptions: {
                bubble: {
                    tooltip: {
                        pointFormat: `<b>Porcentaje de usuarios:</b> {point.z:,.2f}%`
                    }
                }
            },
            series: [
                {
                    showInLegend: false,
                    data,
                    color: colors[colorBurbuja].main,
                    marker: {
                        fillColor: {
                            radialGradient: { cx: 0.4, cy: 0.3, r: 0.7 },
                            stops: [
                                [0, 'rgba(255,255,255,0.5)'],
                                [1, colors[colorBurbuja].main]
                            ]
                        }
                    }
                }
            ],
            credits: {
                enabled: false
            }
        }
        setOptions(options_tmp)
    }, [data, categoriesX, categoriesY, colorBurbuja, tituloX, tituloY])

    //Skins
    const [skin, setSkin] = useSkin()
    const colorTextoDark = '#CDCCCF'
    const colorTextoLight = '#272F44'
    const colorFondoDark = '#272F44'
    const colorFondoLight = 'white'
    // Esto es lo que tienes que cambiar manualmente para los colores del skin

    useEffect(async () => {
        dispatchLoader({tipo: 'llamarAPI'})
        const titulo_enviar = (tituloAPI) ? tituloAPI : titulo // Como la API usa el título de la gráfica para regresar su valor, había un problema cuando ese título es variable, como cuando incluye la fecha actual. Entonces, si desde la vista le mandas el prop tituloAPI, es ese el que se usa para la API. Si lo omites, se usa la variable titulo como estaba pensado originalmente
        const res = await axios({
          method: 'post',
          url: `${CustomUrls.ApiUrl()}burbuja3d/${seccion}?titulo=${titulo_enviar}`,
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
            setCategoriesX(res.data.categoriesX)
            setCategoriesY(res.data.categoriesY)
            setData(res.data.data)
            setTituloX(res.data.tituloX)
            setTituloY(res.data.tituloY)
            setColorBurbuja(res.data.color)
            // console.log(JSON.stringify(res.data.pipeline))
        } else {
            setCategoriesX([])
            setCategoriesY([])
            setData([])
        }
      }, [fechas, region, zona, tienda, proveedor, categoria, tipoEntrega, periodo, agrupador, anioRFM, mesRFM])
    
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

export default Burbuja3D