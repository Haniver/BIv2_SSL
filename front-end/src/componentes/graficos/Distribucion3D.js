// Esto sale de: https://jsfiddle.net/gh/get/library/pure/highcharts/highcharts/tree/master/samples/highcharts/demo/3d-scatter-draggable
// Y: https://codesandbox.io/s/highcharts-scatter-3d-z-axis-issue-demo-d2mpt?file=/demo.jsx
// Y: https://github.com/highcharts/highcharts-react

import React, { useState, useMemo, useRef, useEffect, useContext, useReducer } from "react"
import { render } from "react-dom"
// Import Highcharts
import Highcharts from "highcharts"
import HighchartsReact from "highcharts-react-official"
import highcharts3d from "highcharts/highcharts-3d"
highcharts3d(Highcharts) //init module
require('highcharts/modules/data')(Highcharts)
require('highcharts/modules/exporting')(Highcharts)
require('highcharts/modules/export-data')(Highcharts)
import authHeader from '../../services/auth.header'
import axios from 'axios'
import CustomUrls from '../../services/customUrls'
import { ThemeColors } from '@src/utility/context/ThemeColors'
import { useSkin } from '@hooks/useSkin'
import { Card, CardBody, CardTitle } from 'reactstrap'
import drilldown from 'highcharts/modules/drilldown'
import LoadingGif from '../auxiliares/LoadingGif'
import fechas_srv from '../../services/fechas_srv'
import { conditionallyUpdateScrollbar } from "reactstrap/lib/utils"


const Distribucion3D = ({ titulo, yLabel, seccion, formato, fechas, region, zona, tienda, proveedor, categoria, tipoEntrega, tituloAPI, periodo, agrupador, anioRFM, mesRFM }) => {
    // Highcharts.setOptions({
    //     colors: Highcharts.getOptions().colors.map(function (color) {
    //         return {
    //             radialGradient: {
    //                 cx: 0.4,
    //                 cy: 0.3,
    //                 r: 0.5
    //             },
    //             stops: [
    //                 [0, color],
    //                 [1, Highcharts.color(color).brighten(-0.2).get('rgb')]
    //             ]
    //         }
    //     })
    // })
    const [hayError, setHayError] = useState(false)
    const [data, setData] = useState([])
    const [tituloX, setTituloX] = useState('')
    const [tituloY, setTituloY] = useState('')
    const [tituloZ, setTituloZ] = useState('')
    const [minX, setMinX] = useState(0)
    const [minY, setMinY] = useState(0)
    const [minZ, setMinZ] = useState(0)
    const [maxX, setMaxX] = useState(0)
    const [maxY, setMaxY] = useState(0)
    const [maxZ, setMaxZ] = useState(0)
    const [colorPuntos, setColorPuntos] = useState('')
    const { colors } = useContext(ThemeColors)
    const chartComponent = useRef(null)
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
            renderTo: "container",
            margin: 100,
            type: "scatter3d",
            animation: false,
            options3d: {
              enabled: true,
              alpha: 10,
              beta: 30,
              depth: 250,
              viewDistance: 5,
              fitToPlot: false,
              frame: {
                bottom: { size: 1, color: "rgba(0,0,0,0)" },
                back: { size: 1, color: "rgba(0,0,0,0)" },
                side: { size: 1, color: "rgba(0,0,0,0)" }
              }
            }
            // options3d: {
            //     enabled: true,
            //     alpha: 10,
            //     beta: 30,
            //     depth: 250,
            //     viewDistance: 5,
            //     fitToPlot: false,
            //     frame: {
            //     bottom: { size: 1, color: "rgba(0,0,0,0.02)" },
            //     back: { size: 2, color: "rgba(0,0,0,0.04)" },
            //     side: { size: 3, color: "rgba(0,0,0,0.06)" }
            //     }
            // }
        },
        title: {
            text: "Espera a que carguen los datos"
        },
        subtitle: {
        text: "Arrastra el gráfico para rotarlo"
        },
        plotOptions: {
            scatter: {
                width: 10,
                height: 10,
                depth: 10
            }
        },
        yAxis: {
            min: 0,
            max: 0,
            // gridLineWidth: 1,
            // showFirstLabel: true,
            title: {
                text: ''
            }
        },
        xAxis: {
            min: 0,
            max: 0,
            // gridLineWidth: 1,
            // showFirstLabel: true,
            title: {
                text: ''
            }
        },
        zAxis: {
            min: 0,
            max: 0,
            // gridLineWidth: 1,
            // showFirstLabel: true,
            title: {
                text: ''
            }
        },
        legend: {
            enabled: false
        },
        series: [
        {
            name: "Data",
            colorByPoint: true,
            accessibility: {
            exposeAsGroupOnly: true
            },
            data: []
        }
        ],
        credits: {
            enabled: false
        }
    })
    useEffect(() => {
        const options_tmp = {
            chart: {
                renderTo: "container",
                margin: 100,
                type: "scatter3d",
                animation: false,
                options3d: {
                  enabled: true,
                  alpha: 10,
                  beta: 30,
                  depth: 250,
                  viewDistance: 5,
                  fitToPlot: false,
                  frame: {
                    bottom: { size: 1, color: "rgba(0,0,0,0)" },
                    back: { size: 1, color: "rgba(0,0,0,0)" },
                    side: { size: 1, color: "rgba(0,0,0,0)" }
                  }
                }
                // options3d: {
                //     enabled: true,
                //     alpha: 10,
                //     beta: 30,
                //     depth: 250,
                //     viewDistance: 5,
                //     fitToPlot: false,
                //     frame: {
                //     bottom: { size: 1, color: "rgba(0,0,0,0.02)" },
                //     back: { size: 2, color: "rgba(0,0,0,0.04)" },
                //     side: { size: 3, color: "rgba(0,0,0,0.06)" }
                //     }
                // }
            },
            title: {
                text: titulo
            },
            subtitle: {
            text: "Arrastra el gráfico para rotarlo"
            },
            plotOptions: {
                scatter: {
                    width: 10,
                    height: 10,
                    depth: 10
                }
            },
            xAxis: {
                min: minX,
                max: maxX,
                // showFirstLabel: true,
                // gridLineWidth: 1,
                title: {
                    text: tituloX
                }
            },
            yAxis: {
                min: minY,
                max: maxY,
                // showFirstLabel: true,
                // gridLineWidth: 1,
                title: {
                    text: tituloY
                }
            },
            zAxis: {
                min: minZ,
                max: maxZ,
                // showFirstLabel: true,
                // gridLineWidth: 1,
                title: {
                    text: tituloZ
                }
            },
            legend: {
                enabled: false
            },
            plotOptions: {
                scatter3d: {
                    tooltip: {
                        pointFormat: `<b>${tituloX}: </b>{point.x:,.0f}<br /><b>${tituloY}: </b>$ {point.y:,.2f}<br /><b>${tituloZ}: </b>{point.z:,.0f}`
                    }
                }
            },
            series: [
            {
                name: "Data",
                colorByPoint: true,
                accessibility: {
                exposeAsGroupOnly: true
                },
                data
            }
            ],
            credits: {
                enabled: false
            }
        }
        setOptions(options_tmp)
    }, [data, tituloX, tituloY, tituloZ, minX, minY, minZ, maxX, maxY, maxZ])

    useEffect(() => {
        const chart = chartComponent.current.chart
        function dragStart(eStart) {
            eStart = chart.pointer.normalize(eStart)
    
            const posX = eStart.chartX,
                posY = eStart.chartY,
                alpha = chart.options.chart.options3d.alpha,
                beta = chart.options.chart.options3d.beta,
                sensitivity = 5,  // lower is more sensitive
                handlers = []
    
            function drag(e) {
                // Get e.chartX and e.chartY
                e = chart.pointer.normalize(e)
    
                chart.update({
                    chart: {
                        options3d: {
                            alpha: (alpha + (e.chartY - posY)) / sensitivity,
                            beta: (beta + (posX - e.chartX)) / sensitivity
                        }
                    }
                }, undefined, undefined, false)
            }
    
            function unbindAll() {
                handlers.forEach(function (unbind) {
                    if (unbind) {
                        unbind()
                    }
                })
                handlers.length = 0
            }
    
            handlers.push(Highcharts.addEvent(document, 'mousemove', drag))
            handlers.push(Highcharts.addEvent(document, 'touchmove', drag))
    
    
            handlers.push(Highcharts.addEvent(document, 'mouseup', unbindAll))
            handlers.push(Highcharts.addEvent(document, 'touchend', unbindAll))
        }
        Highcharts.addEvent(chart.container, 'mousedown', dragStart)
        Highcharts.addEvent(chart.container, 'touchstart', dragStart)
    }, [])

    //Skins
    const [skin, setSkin] = useSkin()
    const colorTextoDark = '#CDCCCF'
    const colorTextoLight = '#272F44'
    const colorFondoDark = '#272F44'
    const colorFondoLight = 'white'
    // Esto es lo que tienes que cambiar manualmente para los colores del skin

    useEffect(async () => {
        dispatchLoader({tipo: 'llamarAPI'})
        const tituloEnviar = (tituloAPI) ? tituloAPI : titulo // Como la API usa el título de la gráfica para regresar su valor, había un problema cuando ese título es variable, como cuando incluye la fecha actual. Entonces, si desde la vista le mandas el prop tituloAPI, es ese el que se usa para la API. Si lo omites, se usa la variable titulo como estaba pensado originalmente
        const res = await axios({
            method: 'post',
            url: `${CustomUrls.ApiUrl()}distribucion3d/${seccion}?titulo=${tituloEnviar}`,
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
            // console.log('Data desde Distribucion3D:')
            // console.log(res.data.data)
            setData(res.data.data)
            setTituloX(res.data.tituloX)
            setTituloY(res.data.tituloY)
            setTituloZ(res.data.tituloZ)
            setColorPuntos(res.data.color)
            setMinX(res.data.minX)
            setMinY(res.data.minY)
            setMinZ(res.data.minZ)
            setMaxX(res.data.maxX)
            setMaxY(res.data.maxY)
            setMaxZ(res.data.maxZ)
            // console.log(JSON.stringify(res.data.pipeline))
        } else {
            setData([])
            setTituloX('')
            setTituloY('')
            setTituloZ('')
            setColorPuntos('')
            setMinX(0)
            setMinY(0)
            setMinZ(0)
            setMaxX(0)
            setMaxY(0)
            setMaxZ(0)
        }
    }, [fechas, region, zona, tienda, proveedor, categoria, tipoEntrega, periodo, agrupador, anioRFM, mesRFM])
            
    return (
        <Card>
            <CardBody>
                <HighchartsReact
                    highcharts={Highcharts}
                    options={options}
                    ref={chartComponent}
                    hidden = {estadoLoader.contador !== 0}
                />
                {/* <button onClick={chartComponent.exportChart()}>Exportar</button> */}
                {!hayError && estadoLoader.contador !== 0 && <LoadingGif />}
            </CardBody>
        </Card>
    )
}

export default Distribucion3D
