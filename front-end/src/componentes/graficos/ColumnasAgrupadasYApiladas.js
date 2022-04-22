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

const ColumnasAgrupadasYApiladas = ({ titulo, tituloAPI, seccion, grupoDeptos, deptoAgrupado, subDeptoAgrupado, agrupador, periodo }) => {
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
        console.log("Vamos a mandar datos a la API desde ColumnasAgrupadasYApiladas")
        const res = await axios({
          method: 'post',
          url: `${CustomUrls.ApiUrl()}columnasAgrupadasYApiladas/${seccion}?titulo=${titulo_enviar}`,
          headers: authHeader(),
          data: {
            grupoDeptos, 
            deptoAgrupado,
            periodo, 
            agrupador, 
            subDeptoAgrupado
          }
        })
        dispatchLoader({tipo: 'recibirDeAPI'})
        // console.log("Vamos a recibir datos desde la API a ColumnasAgrupadasYApiladas")
        if (res.data.hayResultados === 'si') {
            const series_tmp = []
            setCategorias(res.data.categorias)
            // console.log(`pipeline ${titulo}: ${JSON.stringify(res.data.pipeline)}`)
            res.data.series.forEach(elemento => {
                series_tmp.push({
                    name: elemento.name,
                    data: elemento.data,
                    stack: elemento.stack,
                    color: elemento.color
                })
            })
            setSeries(series_tmp)
            // console.log('series:')
            // console.log(series_tmp)
        } else {
            // console.log(`hayResultados no es 'si'. Es: ${res.data.hayResultados}`)
            setCategorias([])
            setSeries([])
        }
      }, [grupoDeptos, deptoAgrupado, periodo, subDeptoAgrupado, agrupador, periodo])
    
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
            allowDecimals: false,
            min: 0
        },
        tooltip: {
            pointFormat: '<b>{series.name}</b>: {point.y}'
        },
        legend: {
            enabled: false
        },
        plotOptions: {
            column: {
                stacking: 'normal'
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

export default ColumnasAgrupadasYApiladas