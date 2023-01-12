import { useState, useEffect, useContext, useReducer } from 'react'
import Highcharts from 'highcharts'
import HighchartsReact from 'highcharts-react-official'
import authHeader from '../../services/auth.header'
import axios from 'axios'
import CustomUrls from '../../services/customUrls'
import { ThemeColors } from '@src/utility/context/ThemeColors'
import { useSkin } from '@hooks/useSkin'
import { Card, CardBody, CardTitle } from 'reactstrap'
import drilldown from 'highcharts/modules/drilldown'
import LoadingGif from '../auxiliares/LoadingGif'
import fechas_srv from '../../services/fechas_srv'
import { procesarSerie } from '../../services/funcionesAdicionales'
require('highcharts/modules/data')(Highcharts)
require('highcharts/modules/exporting')(Highcharts)
require('highcharts/modules/export-data')(Highcharts)

const BarrasApiladas = ({ titulo, tituloAPI, yLabel, porcentaje, sinCantidad, seccion, formato, fechas, region, zona, tienda, proveedor, categoria, tipoEntrega, agrupador, periodo, grupoDeptos, deptoAgrupado, subDeptoAgrupado, provLogist }) => {
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

    const [modTitulo, setModTitulo] = useState(titulo)

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

    const tituloEnviar = (tituloAPI !== undefined) ? tituloAPI : titulo
    let stacking = ''
    let pointFormat = ''
    if (porcentaje !== undefined && porcentaje) {
        stacking = 'percent'
        if (sinCantidad !== undefined && sinCantidad) {
            pointFormat = '<span style="color:{series.color}">{series.name}</span>: {point.percentage:.2f}%<br/>'
        } else {
            pointFormat = '<span style="color:{series.color}">{series.name}</span>: <b>{point.y:,.0f}</b> ({point.percentage:.0f}%)<br/>'
        }
    } else {
        stacking = 'normal'
        pointFormat = '<span style="color:{series.color}">{series.name}</span>: <b>{point.y:,.0f}</b><br/>'
    }
    
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
          url: `${CustomUrls.ApiUrl()}barrasApiladas/${seccion}?titulo=${tituloEnviar}`,
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
            periodo, 
            grupoDeptos, 
            deptoAgrupado, 
            subDeptoAgrupado,
            provLogist
          }
        })
        dispatchLoader({tipo: 'recibirDeAPI'})
        if (res.data.hayResultados === 'error') {
            setHayError(true)
        } else if (res.data.hayResultados === 'si') {
        setHayError(false)
            const series_tmp = []
            setCategorias(res.data.categorias)
            // console.log('categorias:')
            // console.log(res.data.categorias)
            res.data.series.forEach(elemento => {
                series_tmp.push({
                    name: elemento.name,
                    data: procesarSerie(elemento.data, formato),
                    color: colors[elemento.color].main
                })
            })
            setSeries(series_tmp)
            if (tituloAPI !== undefined) {
                setModTitulo(res.data.modTitulo)
            }
            // console.log('series:')
            // console.log(series_tmp)
        } else {
            setCategorias([])
            setSeries([])
        }
      }, [fechas, region, zona, tienda, proveedor, categoria, tipoEntrega, agrupador, periodo, grupoDeptos, deptoAgrupado, subDeptoAgrupado, provLogist])
    
    Highcharts.setOptions({
      lang: {
        thousandsSep: ','
      }
    })
    const options = {
        chart: {
            type: 'bar',
            backgroundColor: colorFondo
        },
        title: {
            text: ''
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
            reversedStacks: false,
            title: {
                text: yLabel
            }
        },
        plotOptions: {
            // column: {
            //     stacking: 'percent',
            //     dataLabels: {
            //         enabled: true
            //     }
            // },
            series: {
                dataLabels: {
                    enabled: false,
                    // formatter(tooltip) {
                    //     if (formato === 'moneda') {
                    //         return `$${Highcharts.numberFormat(this.point.y, 2, '.', ',')}`
                    //     } else if (formato === 'entero') {
                    //         return `${Highcharts.numberFormat(this.point.y, 0, '.', ',')}`
                    //     } else if (formato === 'porcentaje') {
                    //         return `${Highcharts.numberFormat(this.point.y * 100, 2, '.', ',')}%`
                    //     }
                    // },
                    color: colorTexto,
                    textOutline: colorTexto
                },
                stacking
            }
        },
        tooltip: {
            pointFormat,
            shared: true
        },
        //     headerFormat: '<b>{point.x}</b><br/>',
        //     formatter(tooltip) {
        //         if (formato === 'moneda') {
        //             return `${this.series.name}: $${Highcharts.numberFormat(this.point.y, 2, '.', ',')}<br/>Total: $${Highcharts.numberFormat(this.point.stackTotal, 2, '.', ',')}`
        //         } else if (formato === 'entero') {
        //             return `${this.series.name}: ${Highcharts.numberFormat(this.point.y, 0, '.', ',')}<br/>Total: ${Highcharts.numberFormat(this.point.stackTotal, 0, '.', ',')}`
        //         } else if (formato === 'porcentaje') {
        //             return `${this.series.name}: ${Highcharts.numberFormat(this.point.y * 100, 2, '.', ',')}%<br/>Total: ${Highcharts.numberFormat(this.point.stackTotal * 100, 2, '.', ',')}%`
        //         }
        //     }
        // },
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
                {hayError && <p classname='texto-rojo'>{`Error en la carga del componente "${titulo}" el ${fechas_srv.fechaYHoraActual()}`}</p>}
                {!hayError && estadoLoader.contador === 0 && <>
                    <CardTitle className='centrado'>{modTitulo}</CardTitle>
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

export default BarrasApiladas