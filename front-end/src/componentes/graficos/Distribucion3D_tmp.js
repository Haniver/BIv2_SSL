// Esto sale de: https://jsfiddle.net/gh/get/library/pure/highcharts/highcharts/tree/master/samples/highcharts/demo/3d-scatter-draggable
// Y: https://codesandbox.io/s/highcharts-scatter-3d-z-axis-issue-demo-d2mpt?file=/demo.jsx
// Y: https://github.com/highcharts/highcharts-react

import React, { useState, useMemo, useRef, useEffect } from "react"
import { render } from "react-dom"
// Import Highcharts
import Highcharts from "highcharts"
import HighchartsReact from "highcharts-react-official"
import highcharts3d from "highcharts/highcharts-3d"
highcharts3d(Highcharts) //init module


const Distribucion3D_tmp = () => {
    Highcharts.setOptions({
        colors: Highcharts.getOptions().colors.map(function (color) {
            return {
                radialGradient: {
                    cx: 0.4,
                    cy: 0.3,
                    r: 0.5
                },
                stops: [
                    [0, color],
                    [1, Highcharts.color(color).brighten(-0.2).get('rgb')]
                ]
            }
        })
    })
    const chartComponent = useRef(null)
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
            bottom: { size: 1, color: "rgba(0,0,0,0.02)" },
            back: { size: 2, color: "rgba(0,0,0,0.04)" },
            side: { size: 3, color: "rgba(0,0,0,0.06)" }
            }
        }
        },
        title: {
        text: "Frecuencia por Monto"
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
        max: 40,
        text: 'Porcentaje de clientes',
        title: 'Porcentaje de clientes',
        label: 'Porcentaje de clientes'
        },
        xAxis: {
        min: 0,
        max: 4,
        gridLineWidth: 1,
        categories: ['$0-$700', '$700-$1,000', '$1,000-$1,500', '$1,500-$2,000', '$2,000+'],
        text: 'Monto',
        title: 'Monto',
        label: 'Monto'
        },
        zAxis: {
        min: 0,
        max: 4,
        showFirstLabel: true,
        categories: ['1-2', '3-5', '6-10', '11-20', '21+'],
        text: 'Frecuencia',
        title: 'Frecuencia',
        label: 'Frecuencia'
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
            data: [
            [0, 0, 31.7339697293224],
            [0, 1, 9.68033661998367],
            [0, 2, 4.00301450731646],
            [0, 3, 1.15932927212209],
            [0, 4, 0.138164918671105],
            [1, 0, 9.06236262010927],
            [1, 1, 4.75161715757081],
            [1, 2, 2.49701689380142],
            [1, 3, 0.91816868680525],
            [1, 4, 0.0766187276267035],
            [2, 0, 8.58757771776675],
            [2, 1, 4.7692017835835],
            [2, 2, 2.69924009294731],
            [2, 3, 1.02116435345098],
            [2, 4, 0.099227532500157],
            [3, 0, 4.1977014381712],
            [3, 1, 2.09382654022483],
            [3, 2, 1.17063367455881],
            [3, 3, 0.395654085285436],
            [3, 4, 0.0326571625949884],
            [4, 0, 7.83520693336683],
            [4, 1, 1.86899453620549],
            [4, 2, 0.889279658355837],
            [4, 3, 0.291402373924512],
            [4, 4, 0.0276329837342209]
            ]
        }
        ]
    })
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

    return (
        <>
        {/* <button
            onClick={() => {
            setDependentStateVar((prev) => ++prev)
            setOptions({
                zAxis: {
                title: {
                    text: dependentStateVar
                }
                }
            })
            }}
        >
            Rerender
        </button> */}
        <HighchartsReact highcharts={Highcharts} options={options} ref={chartComponent} />
        </>
    )
}

export default Distribucion3D_tmp
