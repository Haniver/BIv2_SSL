// https://jsfiddle.net/gh/get/library/pure/highcharts/highcharts/tree/master/samples/highcharts/demo/area-basic
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
import HC_more from 'highcharts/highcharts-more'
HC_more(Highcharts)
require('highcharts/modules/data')(Highcharts)
require('highcharts/modules/exporting')(Highcharts)
require('highcharts/modules/export-data')(Highcharts)

const AreaBasica = ({ titulo, yLabel, seccion, formato, fechas, region, zona, tienda, proveedor, categoria, tipoEntrega, tituloAPI, periodo, agrupador, anioRFM, mesRFM }) => {
    const [data, setData] = useState([])
    const [categories, setCategories] = useState([])
    const [tituloX, setTituloX] = useState('')
    const [tituloY, setTituloY] = useState('')
    const [colorSerie, setColorSerie] = useState('primary')
    const { colors } = useContext(ThemeColors)
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
            type: 'area'
        },
        title: {
            text: 'Espera a que carguen los datos'
        },
        series: [
            {
                name: tituloY,
                color: colors[colorSerie].main,
                data
            }
        ],
        credits: {
            enabled: false
        }
})
    useEffect(() => {
        const options_tmp = {
            chart: {
                type: 'area'
            },
        
            title: {
                text: titulo
            },        
            xAxis: {
                title: {
                    text: tituloX
                },
                categories
            },
            yAxis: {
                title: {
                    text: tituloY
                }
            },
            legend: {
                enabled: false
            },
            tooltip: {
                pointFormat: '{point.y} usuarios'
            },
            series: [
                {
                    name: tituloY,
                    color: colors[colorSerie].main,
                    data
                }
            ],
            credits: {
                enabled: false
            }
        }
        setOptions(options_tmp)
    }, [data, tituloY, categories, colorSerie])

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
          url: `${CustomUrls.ApiUrl()}areaBasica/${seccion}?titulo=${titulo_enviar}`,
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
        if (res.data.hayResultados === 'si') {
            const series_tmp = []
            setCategories(res.data.categories)
            setData(res.data.data)
            setTituloY(res.data.tituloY)
            setTituloX(res.data.tituloX)
            console.log(`Color desde AreaBasica: ${res.data.color} que se traduce a ${colors[colorSerie].main}`)
            setColorSerie(res.data.color)
            // console.log(JSON.stringify(res.data.pipeline))
        } else {
            setCategories([])
            setData([])
            setTituloY('')
        }
      }, [fechas, region, zona, tienda, proveedor, categoria, tipoEntrega, periodo, agrupador, anioRFM, mesRFM])
    
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

export default AreaBasica