import { Button, Alert, Card, CardHeader, CardTitle, CardBody, FormGroup, Input, Label, Row, Col } from 'reactstrap'
import Flatpickr from 'react-flatpickr'
import Select from 'react-select'
import { selectThemeColors } from '@utils'
import { useEffect, useState } from 'react'
import CargarFiltros from '../../services/cargarFiltros'
import fechas_srv from '../../services/fechas_srv'
import '@styles/react/libs/flatpickr/flatpickr.scss'
import { isNumeric } from "validator"
import { nthElement } from '../../services/funcionesAdicionales'
import { Users } from 'react-feather'
import Lupita from '@src/assets/images/lupita.png'
import LoadingGif from './LoadingGif'
import userService from '../../services/user.service'

const Filtro = (props) => {
  // console.log(`Tienda en Filtro=${props.tienda}`)
  const userData = JSON.parse(localStorage.getItem('userData'))
  // if (userData === null || userData === undefined || userData === false) {
  //   return (
  //     <p>No se encontró data de usuario</p>
  //   )
  // }
  // Contar cuántos filtros se van a mostrar en el layout en Bootstrap. Al principio pongo 2 porque el botón de enviar es uno, y al final todo se divide entre 2
  let numElementos = 2
  let bootstrap = {}
  for (const prop in props) {
    if (props.hasOwnProperty(prop)) {
      numElementos += 1
    }
  }
  // console.log(`numElementos (a) = ${numElementos}`)
  // Si están las dos fechas, se agregan dos elemento al layout, porque solo se está contando el prop de fechas, y son dos filtros, por dos (getter y setter)
  if (props.fechas !== undefined && props.fechas.fecha_ini !== '' && props.fechas.fecha_fin !== '') {
    numElementos += 2
  }
  // console.log(`numElementos (b) = ${numElementos}`)
  // Restamos props en el caso de que se esté usando el filtro de año/mes en vez de fecha_ini/fecha_fin. Recuerda que si mandas año/mes, cambia fecha_fin, pero no usas fecha_ini
  if (props.anio !== undefined) {
    numElementos -= 4
  }
  // console.log(`numElementos (c) = ${numElementos}`)
  if (props.anioOpcional !== undefined) {
    numElementos -= 2
  }
  // console.log(`numElementos (d) = ${numElementos}`)
  // Rango Máximo de días es un prop que no se cuenta para el layout
  if (props.rango_max_dias !== undefined) {
    numElementos -= 1
  }
  // console.log(`numElementos (e) = ${numElementos}`)
  // Periodo Label no se cuenta para el layout, y tiene getter y setter
  if (props.setPeriodoLabel !== undefined) {
    numElementos -= 2
  }
  // console.log(`numElementos (f) = ${numElementos}`)

  if (props.cambiarLugar !== undefined) {
    numElementos -= 1
  }
  // console.log(`numElementos (g) = ${numElementos}`)
  if (props.setLabelTienda !== undefined) {
    numElementos -= 1
  }
  // console.log(`numElementos (h) = ${numElementos}`)
  if (props.agrupadorSinDia !== undefined) {
    numElementos -= 1
  }
  // console.log(`numElementos (i) = ${numElementos}`)
  if (props.mismoMes !== undefined) {
    numElementos -= 1
  }
  // console.log(`numElementos (j) = ${numElementos}`)
  if (props.usuario !== undefined) {
    numElementos -= 1
  }
  // Dividimos entre dos el número de elementos porque por cada filtro hay un getter y un setter, entonces se duplican los props
  numElementos = Math.round(numElementos / 2)
  // console.log(`numElementos (k) = ${numElementos}`)
  // Variables del layout de Bootstrap
    if (numElementos === 1) {
      bootstrap = {
        espacio: true,
        xl: 6,
        lg: 6,
        sm: 6,
        xs: 12
      }
    } else if (numElementos === 2) {
      bootstrap = {
        espacio: false,
        xl: 6,
        lg: 6,
        sm: 6,
        xs: 12
      }
    } else if (numElementos === 3) {
      bootstrap = {
        espacio: false,
        xl: 4,
        lg: 4,
        sm: 6,
        xs: 12
      }
    } else if (numElementos === 4) {
      bootstrap = {
        espacio: false,
        xl: 3,
        lg: 3,
        sm: 6,
        xs: 12
      }
    } else if (numElementos === 5) {
      bootstrap = {
        espacio: true,
        xl: 2,
        lg: 2,
        sm: 3,
        xs: 12
      }
    } else if (numElementos === 6) {
      bootstrap = {
        espacio: false,
        xl: 2,
        lg: 2,
        sm: 3,
        xs: 12
      }
    } else if (numElementos === 7) {
      bootstrap = {
        espacio: true,
        xl: 2,
        lg: 2,
        sm: 3,
        xs: 12
      }
    } else if (numElementos === 8) {
      bootstrap = {
        espacio: false,
        xl: 2,
        lg: 2,
        sm: 3,
        xs: 12
      } 
    } else if (numElementos === 9) {
      bootstrap = {
        espacio: false,
        xl: 2,
        lg: 2,
        sm: 3,
        xs: 12
      } 
    } else if (numElementos === 10) {
      bootstrap = {
        espacio: true,
        xl: 2,
        lg: 2,
        sm: 3,
        xs: 12
      } 
    } else if (numElementos === 11) {
      bootstrap = {
        espacio: true,
        xl: 2,
        lg: 2,
        sm: 3,
        xs: 12
      } 
    } else if (numElementos === 12) {
      bootstrap = {
        espacio: true,
        xl: 2,
        lg: 2,
        sm: 3,
        xs: 12
      } 
    } else if (numElementos === 13) {
      bootstrap = {
        espacio: true,
        xl: 2,
        lg: 2,
        sm: 3,
        xs: 12
      } 
    }
  
  // Combos con opciones constantes
  const comboCategoria = [
    {label: 'Chedraui', value: 'Chedraui'},
    {label: 'Zubale', value: 'Zubale'}
  ]

  const comboTipoEntrega = [
    {label: 'Domicilio', value: 'Domicilio'},
    {label: 'Tienda', value: 'Tienda'},
    {label: 'DHL', value: 'DHL'}
  ]

  const comboTipoEntrega2 = [
    {label: 'Premium-Gross', value: 'premium-gross'},
    {label: 'Pickup', value: 'pickup'}
  ]
  
  const comboTipoEntrega3 = [
    {label: 'DHL', value: 'DHL'},
    {label: 'Premium-Gross', value: 'premium-gross'},
    {label: 'Pickup', value: 'pickup'}
  ]

  const comboCanal2 = [
    {label: 'Cornershop', value: 'Cornershop'},
    {label: 'Chedraui', value: 'Chedraui'}
  ]

  const comboOrigen = [
    {label: 'Hybris', value: 'Hybris'},
    {label: 'Vtex', value: 'Vtex'}
  ]

  const comboE3 = [
    {label: '0', value: '0'},
    {label: '1', value: '1'},
    {label: '2', value: '2'}
  ]

  const comboProvLogist = [
    {label: 'Zubale Delivery', value: 'Zubale Delivery'},
    {label: 'Zubale Delivery y Pickup', value: 'Zubale Delivery y Pickup'},
    // {label: 'Depto de Logística', value: 'Logística'},
    {label: 'Recursos Propios', value: 'Recursos Propios'}
  ]

  const comboAnio = []
  const comboAnioOpcional = []
  const comboAnioRFM = [{label: `${fechas_srv.anioActual()}`, value: fechas_srv.anioActual()}]
  const meterMasAnios = Math.abs(2022 - fechas_srv.anioActual())
  for (let i = 0; i <= meterMasAnios; i++) {
    comboAnio.push({label: `${fechas_srv.anioActual() - i}`, value: fechas_srv.anioActual() - i})
    comboAnioOpcional.push({label: `${fechas_srv.anioActual() - 1}`, value: fechas_srv.anioActual() - 1})
    comboAnioRFM.push({label: `${fechas_srv.anioActual() - i - 1}`, value: fechas_srv.anioActual() - i - 1})
  }

  const comboMes = []
  for (let i = 0; i < 12; i++) {
    comboMes.push({label: `${fechas_srv.mesTexto(i, true)}`, value: i})
  }

  const comboMesOpcional = []
  for (let i = 0; i < 12; i++) {
    comboMesOpcional.push({label: `${fechas_srv.mesTexto(i, true)}`, value: i + 1})
  }

  const comboMesRFM = []
  for (let i = 1; i <= 12; i++) {
    comboMesRFM.push({label: `${fechas_srv.mesTexto(i, false)}`, value: i})
  }

  const comboAgrupador = [
    {label: 'Mes', value: 'mes'},
    {label: 'Semana', value: 'semana'},
    {label: 'Día', value: 'dia'}
  ]
  if (props.agrupadorSinDia) {
    comboAgrupador.pop()
  }

  const comboGrupoDeptos = [
    {label: 'Super', value: 'Super'},
    {label: 'MG', value: 'MG'}
  ]
  
  const comboDetalle = [
    {label: 'Día', value: 'dia'},
    {label: 'Timeslot', value: 'timesot'}
  ]
  
  const comboEstatus = [
    {label: 'Entregado', value: 'Entregado'},
    {label: 'No Entregado', value: 'No Entregado'},
    {label: 'Cancelado', value: 'Cancelado'}
  ]

  const comboMetodoEnvio = [
    {label: 'Zubale', value: 'Zubale'},
    {label: 'Recursos Propios', value: 'No es Zubale'}
    // {label: 'Logística', value: 'Logística'}
  ]

  // Hooks para mensajes
  const [mensajeFechas, setMensajeFechas] = useState('')
  const [mensajeSku, setMensajeSku] = useState('')
  // Hooks para combos variables
  const [comboRegion, setComboRegion] = useState([{value:'', label:''}])
  const [comboZona, setComboZona] = useState([{value:'', label:''}])
  const [comboTienda, setComboTienda] = useState([{value:'', label:''}])
  const [comboDepto, setComboDepto] = useState([{value:'', label:''}])
  const [comboDeptoAgrupado, setComboDeptoAgrupado] = useState([{value:'', label:''}])
  const [comboSubDepto, setComboSubDepto] = useState([{value:'', label:''}])
  const [comboSubDeptoAgrupado, setComboSubDeptoAgrupado] = useState([{value:'', label:''}])
  const [comboPeriodo, setComboPeriodo] = useState([{value:'', label:''}])
  const [comboProveedor, setComboProveedor] = useState([{value:'', label:''}])
  const [comboFormato, setComboFormato] = useState([{value:'', label:''}])
  const [comboNps, setComboNps] = useState([{value:'', label:''}])
  const [comboCanal, setComboCanal] = useState([{value:'', label:''}])
  // Hooks para deshabilitar comboboxes
  const [isRegionHidden, setIsRegionHidden] = useState(true)
  const [isZonaDisabled, setIsZonaDisabled] = useState(true)
  const [isZonaHidden, setIsZonaHidden] = useState(false)
  const [isTiendaHidden, setIsTiendaHidden] = useState(true)
  const [isProveedorHidden, setIsProveedorHidden] = useState(true)
  const [isDeptoHidden, setIsDeptoHidden] = useState(true)
  const [isSubDeptoHidden, setIsSubDeptoHidden] = useState(false)
  const [isDeptoAgrupadoHidden, setIsDeptoAgrupadoHidden] = useState(true)
  const [isSubDeptoAgrupadoHidden, setIsSubDeptoAgrupadoHidden] = useState(true)
  const [isFormatoHidden, setIsFormatoHidden] = useState(true)
  const [isNpsHidden, setIsNpsHidden] = useState(true)
  const [isCanalHidden, setIsCanalHidden] = useState(true)
  const [isPeriodoHidden, setIsPeriodoHidden] = useState(true)
  const [isSubDeptoDisabled, setIsSubDeptoDisabled] = useState(true)
  const [isSubDeptoAgrupadoDisabled, setIsSubDeptoAgrupadoDisabled] = useState(true)
  const [isDeptoAgrupadoDisabled, setIsDeptoAgrupadoDisabled] = useState(true)
  const [regionValue, setRegionValue] = useState({value:'', label:''})
  const [zonaValue, setZonaValue] = useState({value:'', label:''})
  // Hooks para valores internos de Filtro
  const [tiendaValue, setTiendaValue] = useState({value:'', label:''})
  const [deptoAgrupadoValue, setDeptoAgrupadoValue] = useState({value:'', label:''})
  const [subDeptoValue, setSubDeptoValue] = useState({value:'', label:''})
  const [subDeptoAgrupadoValue, setSubDeptoAgrupadoValue] = useState({value:'', label:''})
  const [canalValue, setCanalValue] = useState({value:'', label:''})
  const [canal2Value, setCanal2Value] = useState({value:'', label:''})
  const [origenValue, setOrigenValue] = useState({value:'', label:''})
  const [provLogistValue, setProvLogistValue] = useState([])
  const [e3Value, setE3Value] = useState({value:'', label:''})
  const [anioValue, setAnioValue] = useState(comboAnio[0])
  const [anioOpcionalValue, setAnioOpcionalValue] = useState()
  const [anioValueRFM, setAnioValueRFM] = useState(comboAnioRFM[0])
  const [mesValue, setMesValue] = useState(comboMes[fechas_srv.mesActual()])
  const [mesOpcionalValue, setMesOpcionalValue] = useState()
  const [mesValueRFM, setMesValueRFM] = useState(comboMesRFM[fechas_srv.mesActual()])
  const [agrupadorValue, setAgrupadorValue] = useState(comboAgrupador[comboAgrupador.findIndex(x => x.value === props.agrupador)])
  const [grupoDeptosValue, setGrupoDeptosValue] = useState(comboGrupoDeptos[comboGrupoDeptos.findIndex(x => x.value === props.grupoDeptos)])
  const [periodoValue, setPeriodoValue] = useState({label: '', value: {}})
  const [detalleValue, setDetalleValue] = useState(comboDetalle[0])
  const [tipoEntrega2Value, setTipoEntrega2Value] = useState(comboTipoEntrega2[0])
  const [formatoValue, setFormatoValue] = useState({value:'', label:''})
  const [npsValue, setNpsValue] = useState({value:'', label:''})
  const [skuValue, setSkuValue] = useState('')
  // Hook para bloquear el botón Enviar si el filtro no está listo
  const [bloqueadoBotonEnviar, setBloqueadoBotonEnviar] = useState(true)
  // Hooks para valores temporales de fecha_ini y fin
  const [fecha_ini_tmp, setFecha_ini_tmp] = useState(() => {
    if (props.fechas !== undefined) {
      if (props.fechas.fecha_ini !== '') {
        return props.fechas.fecha_ini
      } else {
        return props.fechas.fecha_fin
      }
    } else {
      return ''
    }
  })
  const [fecha_fin_tmp, setFecha_fin_tmp] = useState(() => {
    if (props.fechas !== undefined) {
      if (props.fechas.fecha_fin !== '') {
        return props.fechas.fecha_fin
      } else {
        return props.fechas.fecha_ini
      }
    } else {
      return ''
    }
  })
  // Hooks para valores temporales de todos los filtros cuando se usa botonEnviar
      const [Region_tmp, setRegion_tmp] = useState(props.region)
      const [Zona_tmp, setZona_tmp] = useState(props.zona)
    const [Tienda_tmp, setTienda_tmp] = useState(props.tienda)
      const [Depto_tmp, setDepto_tmp] = useState(props.depto)
      const [SubDepto_tmp, setSubDepto_tmp] = useState(props.subDepto)
      const [Periodo_tmp, setPeriodo_tmp] = useState(props.periodo)
      const [Fechas_tmp, setFechas_tmp] = useState(props.fechas)
      const [Agrupador_tmp, setAgrupador_tmp] = useState(props.agrupador)
      const [LabelTienda_tmp, setLabelTienda_tmp] = useState(props.labelTienda)
      const [Sku_tmp, setSku_tmp] = useState(props.sku)
      const [Detalle_tmp, setDetalle_tmp] = useState(props.detalle)
      const [TipoEntrega_tmp, setTipoEntrega_tmp] = useState(props.tipoEntrega)
      const [TipoEntrega2_tmp, setTipoEntrega2_tmp] = useState(props.tipoEntrega2)
      const [TipoEntrega3_tmp, setTipoEntrega3_tmp] = useState(props.tipoEntrega3)
      const [Estatus_tmp, setEstatus_tmp] = useState(props.estatus)
      const [MetodoEnvio_tmp, setMetodoEnvio_tmp] = useState(props.metodoEnvio)
      const [Formato_tmp, setFormato_tmp] = useState(props.formato)
      const [Canal_tmp, setCanal_tmp] = useState(props.canal)
      const [Canal2_tmp, setCanal2_tmp] = useState(props.canal2)
      const [Origen_tmp, setOrigen_tmp] = useState(props.origen)
      const [ProvLogist_tmp, setProvLogist_tmp] = useState(props.provLogist)
      const [E3_tmp, setE3_tmp] = useState(props.e3)
      const [Proveedor_tmp, setProveedor_tmp] = useState(props.proveedor)
      const [Categoria_tmp, setCategoria_tmp] = useState(props.categoria)
      const [Anio_tmp, setAnio_tmp] = useState(props.anio)
      const [AnioOpcional_tmp, setAnioOpcional_tmp] = useState(props.anioOpcional)
      const [Mes_tmp, setMes_tmp] = useState(props.mes)
      const [MesOpcional_tmp, setMesOpcional_tmp] = useState(props.mesOpcional)
      const [PeriodoLabel_tmp, setPeriodoLabel_tmp] = useState(props.periodoLabel)
      const [Nps_tmp, setNps_tmp] = useState(props.nps)
  // Funciones para rellenar combos dependiendo de los valores de otros combos
  const handleRegionChange = async (e) => {
    setIsTiendaHidden(true)
    if (e) {
      setRegionValue({label: e.label, value: e.value})
      if (props.botonEnviar === undefined) {
        props.setRegion(e.value)
      } else {
        setRegion_tmp(e.value)
      }
      setIsZonaHidden(true)
      setBloqueadoBotonEnviar(true)
      const comboZona_temp = await CargarFiltros.cargarZona(e.value)
      setComboZona(comboZona_temp)
      setIsZonaHidden(false)
      setIsZonaDisabled(false)
      setIsTiendaHidden(true)
      const comboTienda_temp = await CargarFiltros.cargarTienda(e.value, undefined)
      setComboTienda(comboTienda_temp)
      setIsTiendaHidden(false)
      setBloqueadoBotonEnviar(false)
    } else {
      setTiendaValue({label: '', value: ''})
      if (props.botonEnviar === undefined) {
        props.setTienda('')
      } else {
        setTienda_tmp('')
      }
      setZonaValue({label: '', value: ''})
      if (props.botonEnviar === undefined) {
        // console.log("Poniendo zona en '' desde 1 (handleRegionChange)")
        // console.log(e)
        props.setZona('')
      } else {
        setZona_tmp('')
      }
      setRegionValue({value:'', label:''})
      setComboZona([{value:'', label:''}])
      if (props.botonEnviar === undefined) {
        props.setRegion('')
      } else {
        setRegion_tmp('')
      }
      setIsTiendaHidden(true)
      setBloqueadoBotonEnviar(true)
      const comboTienda_temp = await CargarFiltros.cargarTienda(undefined, undefined)
      setComboTienda(comboTienda_temp)
      setIsTiendaHidden(false)
      setBloqueadoBotonEnviar(false)
    }
    setIsTiendaHidden(false)
  }

  const handleZonaChange = async (e) => {
    setIsTiendaHidden(true)
    if (e) {
      if (props.botonEnviar === undefined) {
        // console.log("cambiando zona desde 2 con e:")
        // console.log(e)
        props.setZona(e.value)
      } else {
        setZona_tmp(e.value)
      }
      setIsTiendaHidden(true)
      setBloqueadoBotonEnviar(true)
      const comboTienda_temp = await CargarFiltros.cargarTienda(props.region, e.value)
      setComboTienda(comboTienda_temp)
      setIsTiendaHidden(false)
      setZonaValue({label: e.label, value: e.value})
      setBloqueadoBotonEnviar(false)
    } else {
      if (props.botonEnviar === undefined) {
        // console.log("cambiando zona desde 3")
        props.setZona('')
      } else {
        setZona_tmp('')
      }
      setZonaValue({label: '', value: ''})
      setIsTiendaHidden(true)
      setBloqueadoBotonEnviar(true)
      const comboTienda_temp = await CargarFiltros.cargarTienda(props.region, undefined)
      setComboTienda(comboTienda_temp)
      setIsTiendaHidden(false)
      setBloqueadoBotonEnviar(false)
    }
    setTiendaValue({label: '', value: ''})
    setIsTiendaHidden(false)
    setIsZonaDisabled(false)
    if (props.botonEnviar === undefined) {
      props.setTienda('')
    } else {
      setTienda_tmp('')
    }
  }

  const handleTiendaChange = async (e) => {
    if (e) {
      setBloqueadoBotonEnviar(true)
      const regionYZona = await CargarFiltros.getRegionYZona(e.value)
      if (regionValue.value === undefined || regionValue.value === '') {
        await handleRegionChange(regionYZona.data.region)
        setRegionValue({label: regionYZona.data.region.label, value: regionYZona.data.region.value})
        setIsRegionHidden(false)
      }
      if (zonaValue.value === undefined || zonaValue.value === '') {
        await handleZonaChange(regionYZona.data.zona)
        setIsZonaHidden(false)
        setZonaValue({label: regionYZona.data.zona.label, value: regionYZona.data.zona.value})
      }
      setTiendaValue({label: e.label, value: e.value})
      if (props.botonEnviar === undefined) {
        props.setTienda(e.value)
      } else {
        setTienda_tmp(e.value)
      }
      if (props.setLabelTienda !== undefined) {
        // props.setLabelTienda(e.label)
        setLabelTienda_tmp(e.label)
      }
      setBloqueadoBotonEnviar(false)
    } else {
      setTiendaValue({label: '', value: ''})
      if (props.botonEnviar === undefined) {
        props.setTienda('')
      } else {
        setTienda_tmp('')
      }
    }
  }

  useEffect(async () => {
    if (props.cambiarLugar !== undefined && props.cambiarLugar !== false) {
      // console.log('Llamando a handleRegionChange')
      await handleRegionChange(props.cambiarLugar.region)
      await handleZonaChange(props.cambiarLugar.zona)
      await handleTiendaChange(props.cambiarLugar.tienda)
    }
  }, [props.cambiarLugar])
  
  const cambiaGrupoDeptos = async (e) => {
    // setGrupoDeptosValue(e)
    // if (props.botonEnviar === undefined) {
    //   props.setGrupoDeptos(e.value)
    // } else {
    //   setGrupoDeptos_tmp(e.value)
    // }
    // if (e.value === 'Super') {
    //   // Ponerle los deptos de super
    //   setComboDeptoAgrupado(
    //     [
    //      {label: 'PGC Comestible (1)', value: 1}, 
    //      {label: 'PGC No Comestible (90)', value: 90}, 
    //      {label: 'Perecederos No Transformacion (91)', value: 91}, 
    //      {label: 'Transformacion y Alimentos (2)', value: 2}, 
    //      {label: 'Variedades (7)', value: 7}
    //   ]
    //   )
    // } else if (e.value === 'MG') {
    //   // Ponerle los deptos del otro que no es super
    //   setComboDeptoAgrupado(
    //     [
    //     {label: 'Electro-muebles (6)', value: 6}, 
    //     {label: 'MISCELANEOS (9)', value: 9},
    //     {label: 'Ropa, Zapatería y Te (4)', value: 4}
    //   ]
    //   )
    // } else {
    //   setComboDeptoAgrupado(
    //     [{label: '', value: ''}]
    //   )
    // }
    if (e) {
      props.setGrupoDeptos(e.value)
      setIsDeptoAgrupadoHidden(true)
      setBloqueadoBotonEnviar(true)
      const comboDeptoAgrupado_temp = await CargarFiltros.cargarDeptoAgrupado(e.value)
      setComboDeptoAgrupado(comboDeptoAgrupado_temp)
      setIsDeptoAgrupadoHidden(true)
      setIsDeptoAgrupadoDisabled(false)
      setBloqueadoBotonEnviar(false)
    } else {
      setComboDeptoAgrupado([{value:'', label:''}])
      props.setGrupoDeptos('')
      setIsDeptoAgrupadoDisabled(true)
      setIsSubDeptoAgrupadoDisabled(true)
    }
    setDeptoAgrupadoValue({label: '', value: ''})
    props.setDeptoAgrupado('')
    setSubDeptoAgrupadoValue({label: '', value: ''})
    props.setSubDeptoAgrupado('')
  }
  
  const handleDeptoAgrupadoChange = async (e) => {
    if (e) {
      props.setDeptoAgrupado(e.value)
      setDeptoAgrupadoValue({label: e.label, value: e.value})
      setIsSubDeptoAgrupadoDisabled(true)
      setIsSubDeptoAgrupadoHidden(true)
      setBloqueadoBotonEnviar(true)
      const comboSubDeptoAgrupado_temp = await CargarFiltros.cargarSubDeptoAgrupado(e.value)
      setComboSubDeptoAgrupado(comboSubDeptoAgrupado_temp)
      setIsSubDeptoAgrupadoDisabled(false)
      setIsSubDeptoAgrupadoHidden(false)
      setBloqueadoBotonEnviar(false)
    } else {
      setDeptoAgrupadoValue({label: '', value: ''})
      setComboSubDeptoAgrupado([{value:'', label:''}])
      props.setDeptoAgrupado('')
      setIsSubDeptoAgrupadoDisabled(true)
    }
    setSubDeptoAgrupadoValue({label: '', value: ''})
    props.setSubDeptoAgrupado('')
  }

  const handleSubDeptoAgrupadoChange = async (e) => {
    setIsSubDeptoAgrupadoDisabled(false)
    if (e) {
      setSubDeptoAgrupadoValue({label: e.label, value: e.value})
      props.setSubDeptoAgrupado(e.value)
    } else {
      setSubDeptoAgrupadoValue({label: '', value: ''})
      props.setSubDeptoAgrupado('')
    }
  }

  const handleDeptoChange = async (e) => {
    if (e) {
      if (props.botonEnviar === undefined) {
        props.setDepto(e.value)
      } else {
        setDepto_tmp(e.value)
      }
      setIsSubDeptoHidden(true)
      setBloqueadoBotonEnviar(true)
      const comboSubDepto_temp = await CargarFiltros.cargarSubDepto(e.value)
      setComboSubDepto(comboSubDepto_temp)
      setIsSubDeptoHidden(false)
      setIsSubDeptoDisabled(false)
      setBloqueadoBotonEnviar(false)
    } else {
      setComboSubDepto([{value:'', label:''}])
      if (props.botonEnviar === undefined) {
        props.setDepto('')
      } else {
        setDepto_tmp('')
      }
      setIsSubDeptoDisabled(true)
    }
    setSubDeptoValue({label: '', value: ''})
    if (props.botonEnviar === undefined) {
      props.setSubDepto('')
    } else {
      setSubDepto_tmp('')
    }
  }

  const handleSubDeptoChange = async (e) => {
    setIsSubDeptoDisabled(false)
    if (e) {
      setSubDeptoValue({label: e.label, value: e.value})
      if (props.botonEnviar === undefined) {
        props.setSubDepto(e.value)
      } else {
        setSubDepto_tmp(e.value)
      }
    } else {
      setSubDeptoValue({label: '', value: ''})
      if (props.botonEnviar === undefined) {
        props.setSubDepto('')
      } else {
        setSubDepto_tmp('')
      }
    }
  }

  const resetPeriodo = async () => {
    setPeriodoValue({label: '', value: {}})
    // props.setPeriodo({})
  }

  const cambiaFecha_ini = async (value) => {
    if (props.periodo !== undefined) {
      setBloqueadoBotonEnviar(true)
      resetPeriodo()
    }
    // To calculate the time difference of two dates
    const Difference_In_Time = fecha_fin_tmp.getTime() - value.getTime()
    // To calculate the no. of days between two dates
    const Difference_In_Days = Difference_In_Time / (1000 * 3600 * 24)
    if (Difference_In_Days >= 0) {
      if (props.rango_max_dias !== undefined) {
        if (parseInt(Difference_In_Days) > parseInt(props.rango_max_dias)) {
          setMensajeFechas(`La fecha final no debe ser más de ${props.rango_max_dias} días mayor a la inicial`)
        } else {
          setMensajeFechas('')
          if (props.botonEnviar === undefined) {
            props.setFechas({fecha_ini: value, fecha_fin: fecha_fin_tmp})
          } else {
            setFechas_tmp({fecha_ini: value, fecha_fin: fecha_fin_tmp})
          }
        }
      } else {
        setMensajeFechas('')
        if (props.botonEnviar === undefined) {
          props.setFechas({fecha_ini: value, fecha_fin: fecha_fin_tmp})
        } else {
          setFechas_tmp({fecha_ini: value, fecha_fin: fecha_fin_tmp})
        }
      }
      if (props.mismoMes !== undefined) {
        if (value.getMonth() !== fecha_fin_tmp.getMonth()) {
          setMensajeFechas(`Para este dashboard, la fecha inicial y la final deben de estar en el mismo mes`)
        } else {
          setMensajeFechas('')
          if (props.botonEnviar === undefined) {
            props.setFechas({fecha_ini: value, fecha_fin: fecha_fin_tmp})
          } else {
            setFechas_tmp({fecha_ini: value, fecha_fin: fecha_fin_tmp})
          }
        }
      } else {
        setMensajeFechas('')
        if (props.botonEnviar === undefined) {
          props.setFechas({fecha_ini: value, fecha_fin: fecha_fin_tmp})
        } else {
          setFechas_tmp({fecha_ini: value, fecha_fin: fecha_fin_tmp})
        }
      }
    } else {
      setMensajeFechas('La fecha final debe ser mayor a la inicial')
    }
    setFecha_ini_tmp(value)
  }
  
  const cambiaFecha_fin = async (value) => {
    if (props.periodo !== undefined) {
      setBloqueadoBotonEnviar(true)
      resetPeriodo()
    }
    // To calculate the time difference of two dates
    const Difference_In_Time = value.getTime() - fecha_ini_tmp.getTime()
    // To calculate the no. of days between two dates
    const Difference_In_Days = Difference_In_Time / (1000 * 3600 * 24)
    if (Difference_In_Days >= 0) {
      if (props.rango_max_dias !== undefined) {
        if (parseInt(Difference_In_Days) > parseInt(props.rango_max_dias)) {
          setMensajeFechas(`La fecha final no debe ser más de ${props.rango_max_dias} días mayor a la inicial`)
        } else {
          setMensajeFechas('')
          if (props.botonEnviar === undefined) {
            props.setFechas({fecha_ini: fecha_ini_tmp, fecha_fin: value})
          } else {
            setFechas_tmp({fecha_ini: fecha_ini_tmp, fecha_fin: value})
          }
        }
      } else {
        setMensajeFechas('')
        if (props.botonEnviar === undefined) {
          props.setFechas({fecha_ini: fecha_ini_tmp, fecha_fin: value})
        } else {
          setFechas_tmp({fecha_ini: fecha_ini_tmp, fecha_fin: value})
        }
      }
      if (props.mismoMes !== undefined) {
        if (parseInt(Difference_In_Days) > parseInt(props.rango_max_dias)) {
          setMensajeFechas(`Para este dashboard, la fecha inicial y la final deben de estar en el mismo mes`)
        } else {
          setMensajeFechas('')
          if (props.botonEnviar === undefined) {
            props.setFechas({fecha_ini: fecha_ini_tmp, fecha_fin: value})
          } else {
            setFechas_tmp({fecha_ini: fecha_ini_tmp, fecha_fin: value})
          }
        }
      } else {
        setMensajeFechas('')
        if (props.botonEnviar === undefined) {
          props.setFechas({fecha_ini: fecha_ini_tmp, fecha_fin: value})
        } else {
          setFechas_tmp({fecha_ini: fecha_ini_tmp, fecha_fin: value})
        }
      }
    } else {
      setMensajeFechas('La fecha final debe ser mayor a la inicial')
    }
    setFecha_fin_tmp(value)
  }
  
  // Este es la variable que indica si es la primera vez que cambia el periodo
  const [primeraCargaPeriodo, setPrimeraCargaPeriodo] = useState(true)
  // Esta es la función helper para hacer el cambio de Periodo. Si es la primera vez que se cambia el periodo o no hay botonEnviar, se cambia el prop. Si no, se pone en una variable temporal.
  const cambiaPeriodo  = (e = undefined) => {
    if (e !== undefined) {
      const valor = (e) ? e.value : ''
      setPeriodo_tmp(valor)
      if (props.setPeriodoLabel !== undefined) {
        // props.setPeriodoLabel(e.label.substring(0, e.label.length - 5))
        setPeriodoLabel_tmp(e.label.substring(0, e.label.length - 5))
      }
      setPeriodoValue(e)
    } else {
      // console.log("Entró a cambiarPeriodo con e === undefined")
      // if (primeraCargaPeriodo) {
      if (comboPeriodo.length > 0 && comboPeriodo[comboPeriodo.length - 1].value !== '') {
        if (props.setPeriodoLabel !== undefined) {
          const label_tmp = nthElement(comboPeriodo, -1).label
          // props.setPeriodoLabel(label_tmp.substring(0, label_tmp.length - 5))
          setPeriodoLabel_tmp(label_tmp.substring(0, label_tmp.length - 5))
        }
        // console.log("comboPeriodo.length > 0:")
        // console.log(comboPeriodo)
        let posicionElemento = -1
        if (props.agrupador === 'semana') {
          posicionElemento = -2
        }
        if (primeraCargaPeriodo) {
          // console.log("Es la primera carga de periodo")
          if (props.setPeriodoLabel !== undefined) {
            // props.setPeriodoLabel(e.label.substring(0, e.label.length - 5))
            props.setPeriodoLabel(nthElement(comboPeriodo, posicionElemento).label.substring(0, nthElement(comboPeriodo, posicionElemento).label.length - 5))
            setPeriodoLabel_tmp(nthElement(comboPeriodo, posicionElemento).label.substring(0, nthElement(comboPeriodo, posicionElemento).label.length - 5))
          }
          props.setPeriodo(nthElement(comboPeriodo, posicionElemento).value)
          setPeriodo_tmp(nthElement(comboPeriodo, posicionElemento).value)
          setPrimeraCargaPeriodo(false)
        } else {
          // console.log("No es la primera carga de periodo")
          setPeriodo_tmp(nthElement(comboPeriodo, posicionElemento).value)
        }
        setPeriodoValue(nthElement(comboPeriodo, posicionElemento))
      }
    }
    setBloqueadoBotonEnviar(false)
  }
  const cambiaAgrupador = async (e) => {
    if (props.periodo !== undefined) {
      setBloqueadoBotonEnviar(true)
    }
    resetPeriodo()
    setAgrupadorValue(e)
    setAgrupador_tmp(e.value)
    // cambiaPeriodo()
  }
  
  // Cargar el combo periodo
  useEffect(async () => {
    if (props.periodo !== undefined) {
      if (props.fechas !== undefined) {
        // console.log(`Va a cambiar comboPeriodo por lo correspondiente a ${Agrupador_tmp} con fechas:`)
        // console.log(Fechas_tmp)
        setIsPeriodoHidden(true)
        setBloqueadoBotonEnviar(true)
        const comboPeriodo_temp = await CargarFiltros.cargarPeriodo(Agrupador_tmp, Fechas_tmp)
        setComboPeriodo(comboPeriodo_temp)
        setIsPeriodoHidden(false)
        setBloqueadoBotonEnviar(false)
      } else {
        let fechas_tmp = {}
        const currentDate = new Date()
        if (props.agrupador === 'semana') {
          // fechas_tmp = {fecha_ini: new Date('2000-01-01'), fecha_fin: new Date(currentDate.setDate(currentDate.getDate() - 7))} // Le quitamos la semana vencida porque ahora en el dashboard catalogoArticulos queremos que se muestre semana y mes corrientes
          fechas_tmp = {fecha_ini: new Date('2000-01-01'), fecha_fin: new Date(currentDate.setDate(currentDate.getDate()))}
        } else if (props.agrupador === 'mes') {
          fechas_tmp = {fecha_ini: new Date('2000-01-01'), fecha_fin: new Date(currentDate.setMonth(currentDate.getMonth() - 1))} 
        }
        setIsPeriodoHidden(true)
        setBloqueadoBotonEnviar(true)
        const comboPeriodo_temp = await CargarFiltros.cargarPeriodo(Agrupador_tmp, fechas_tmp)
        setComboPeriodo(comboPeriodo_temp)
        setIsPeriodoHidden(false)
        setBloqueadoBotonEnviar(false)
      }
    }    
  }, [Agrupador_tmp, fecha_ini_tmp, fecha_fin_tmp])

  // Esto es lo que pasa cada vez que cambia comboPeriodo. Se manda a llamar cambiaPeriodo sin evento.
  useEffect(() => {
    cambiaPeriodo()
  }, [comboPeriodo])


  useEffect(() => {
    if (props.nps !== undefined) {
      setNpsValue(comboNps[0])
      props.setNps(comboNps[0].value)
      setNps_tmp(comboNps[0].value)
    }
  }, [comboNps])

  // Rellenado inicial de combos variables

  // Rellenado inicial de combos de lugar
  useEffect(async () => {
    if (props.usuario === undefined) { // O sea, hay userData y no estamos en Alta de Usuarios
      // Llenar región
      setBloqueadoBotonEnviar(true)
      if (!props.region && userService.getNivel() >= 4) { // La región te la puedo mostrar en dos escenarios: ya accediste al BI y tienes nivel 4 o 5, o te estás registrando y no tienes userData
        setIsRegionHidden(true)
        const comboRegion_temp = await CargarFiltros.cargarRegion()
        setComboRegion(comboRegion_temp)
        setIsRegionHidden(false)
        setIsZonaDisabled(true)
        const comboTienda_temp = await CargarFiltros.cargarTienda(undefined, undefined)
        setComboTienda(comboTienda_temp)
        setIsTiendaHidden(false)
      }

      if (userService.getNivel() === 3) {
        setIsZonaHidden(true)
        const comboZona_temp = await CargarFiltros.cargarZona(userService.getRegion())
        setComboZona(comboZona_temp)
        setIsZonaHidden(false)
      }

      if (userService.getNivel() === 2) {
        setIsTiendaHidden(true)
        const comboTienda_temp = await CargarFiltros.cargarTienda(userService.getRegion(), userService.getZona())
        setComboTienda(comboTienda_temp)
        setIsTiendaHidden(false)

      }
      setBloqueadoBotonEnviar(false)
      if (props.setLabelTienda !== undefined && props.tienda !== undefined && userService.getNivel() === 1) {
        // props.setLabelTienda(userService.getLugarNombre())
        setLabelTienda_tmp(userService.getLugarNombre())
      }
      if (props.proveedor !== undefined) {
        setIsProveedorHidden(true)
        setBloqueadoBotonEnviar(true)
        const comboProveedor_temp = await CargarFiltros.cargarProveedor()
        setComboProveedor(comboProveedor_temp)
        setIsProveedorHidden(false)
        setBloqueadoBotonEnviar(false)
      }
      if (props.depto !== undefined) {
        setIsDeptoHidden(true)
        setBloqueadoBotonEnviar(true)
        const comboDepto_temp = await CargarFiltros.cargarDepto()
        setComboDepto(comboDepto_temp)
        setIsDeptoHidden(false)
        setBloqueadoBotonEnviar(false)
      }
      if (props.formato !== undefined) {
        setIsFormatoHidden(true)
        setBloqueadoBotonEnviar(true)
        const comboFormato_temp = await CargarFiltros.cargarFormato()
        setComboFormato(comboFormato_temp)
        setIsFormatoHidden(false)
        setBloqueadoBotonEnviar(false)
      }
      if (props.nps !== undefined) {
        setIsNpsHidden(true)
        setBloqueadoBotonEnviar(true)
        const comboNps_temp = await CargarFiltros.cargarNps()
        setComboNps(comboNps_temp)
        setIsNpsHidden(false)
        setBloqueadoBotonEnviar(false)
      }
      if (props.canal !== undefined) {
        setIsCanalHidden(true)
        setBloqueadoBotonEnviar(true)
        const comboCanal_temp = await CargarFiltros.cargarCanal()
        setComboCanal(comboCanal_temp)
        setIsCanalHidden(false)
        setBloqueadoBotonEnviar(false)
      }
      if (props.origen !== undefined) {
        setOrigenValue(comboOrigen[1])
      }
    }
  }, [])

  // Esto es solo para cuando se usa el filtro en el Alta de Usuarios
  useEffect(async () => {
    if (props.usuario && props.usuario.tienda) {
      // console.log(`(region, zona, tienda) = (${props.region}, ${props.zona}, ${props.tienda})`)
      // Rellenar región del usuario
      setIsRegionHidden(true)
      setBloqueadoBotonEnviar(true)
      const comboRegion_temp = await CargarFiltros.cargarRegion()
      setComboRegion(comboRegion_temp)
      setIsRegionHidden(false)
      setBloqueadoBotonEnviar(false)
      const idx_regionNombre = comboRegion_temp.findIndex(object => {
        return object.value === props.region
      })
      if (idx_regionNombre >= 0) {
        const regionNombre = comboRegion_temp[idx_regionNombre].label
        setRegionValue({label: regionNombre, value: props.region})
      }
      // Rellenar zona del usuario 
      setIsZonaDisabled(false)
      setIsZonaHidden(true)
      setBloqueadoBotonEnviar(true)
      const comboZona_temp = await CargarFiltros.cargarZona(props.region)
      setComboZona(comboZona_temp)
      setIsZonaHidden(false)
      setBloqueadoBotonEnviar(false)
      const idx_zonaNombre = comboZona_temp.findIndex(object => {
        return object.value === props.zona
      })
      if (idx_zonaNombre >= 0) {
        const zonaNombre = comboZona_temp[idx_zonaNombre].label
        setZonaValue({label: zonaNombre, value: props.zona})
      }
      // Rellenar Tienda del usuario 
      setIsTiendaHidden(true)
      setBloqueadoBotonEnviar(true)
      const comboTienda_temp = await CargarFiltros.cargarTienda(props.region, props.zona)
      setComboTienda(comboTienda_temp)
      setIsTiendaHidden(false)
      setBloqueadoBotonEnviar(false)
      const idx_tiendaNombre = comboTienda_temp.findIndex(object => {
        return object.value === props.tienda
      })
      if (idx_tiendaNombre >= 0) {
        const tiendaNombre = comboTienda_temp[idx_tiendaNombre].label
        setTiendaValue({label: tiendaNombre, value: props.tienda})
      }
    }
  }, [props.usuario])

  // Poner valor inicial para canal
  useEffect(() => {
    setCanalValue(nthElement(comboCanal, -1))
    // props.setCanal(nthElement(comboCanal, -1).value)
  }, [comboCanal])

  // Validar que SKU sea numérico
  useEffect(async () => {
    if (props.sku !== undefined) {
      if (!isNumeric(skuValue) && skuValue !== '') {
        setMensajeSku('Este no es un número válido')
      } else {
        setMensajeSku('')
        if (props.botonEnviar === undefined) {
          props.setSku(skuValue)
        } else {
          setSku_tmp(skuValue)
        }
      }
    }
  }, [skuValue])
  
  // Layout
  return (
    <>
    {/* <Card> */}
      {/* {userData !== null && userData !== undefined && userData !== false && (props.usuario === null || props.usuario === undefined || props.usuario === false) && <CardHeader>
      <CardTitle tag='h4'>Filtros</CardTitle>
      </CardHeader>} */}
      {userData !== null && userData !== undefined && userData !== false && (props.usuario === null || props.usuario === undefined || props.usuario === false) && <h4 className='tituloFiltro'>
        Filtros
      </h4>}

      {/* <CardBody> */}
        <Row>
          {props.sku !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>🏷 SKU</Label>
            <Input 
              type='text' 
              id='filtroSku' 
              placeholder='00000000' 
              onBlur={
                e => setSkuValue(e.target.value)
              } 
            />
            <Alert color="danger">
              {mensajeSku}
            </Alert>
          </Col>}
          { 
            props.fechas !== undefined && props.fechas.fecha_ini !== '' && props.anio === undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <FormGroup>
              <Label for='fecha_ini'>Fecha Inicial</Label>
              <Flatpickr className="form-control" value={props.fechas.fecha_ini} onChange={(e) => cambiaFecha_ini(e[0])}  id="fecha_ini" options={{ dateFormat: "Y-m-d" }} />
            </FormGroup>
          </Col>}
          { /* Si existe props.anio y props.mes, fecha_fin se usa pero no se muestra */
            props.fechas !== undefined && props.fechas.fecha_fin !== '' && props.mes === undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <FormGroup>
              <Label for='fecha_fin'>Fecha Final</Label>
              <Flatpickr className="form-control" value={props.fechas.fecha_fin} onChange={(e) => cambiaFecha_fin(e[0])}  id="fecha_fin" options={{ dateFormat: "Y-m-d" }} />
            </FormGroup>
            <Alert color="danger">
              {mensajeFechas}
            </Alert>
          </Col>}
          {props.detalle !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Detalle</Label>
            <Select
              theme={selectThemeColors}
              value={detalleValue}
              className='react-select'
              classNamePrefix='select'
              name='filtroDetalle'
              options={comboDetalle}
              // isClearable={true}
              onChange={e => {
                if (props.botonEnviar === undefined) {
                  props.setDetalle(e.value)
                } else {
                  setDetalle_tmp(e.value)
                }
                setDetalleValue(e)
              }}
            />
          </Col>}
          {props.tipoEntrega2 !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Tipo de Entrega</Label>
            <Select
              theme={selectThemeColors}
              value={tipoEntrega2Value}
              className='react-select'
              classNamePrefix='select'
              name='filtroTipoEntrega2'
              options={comboTipoEntrega2}
              // isClearable={true}
              onChange={e => {
                if (props.botonEnviar === undefined) {
                  props.setTipoEntrega2(e.value)
                } else {
                  setTipoEntrega2_tmp(e.value)
                }
                setTipoEntrega2Value(e)
              }}
            />
          </Col>}
          {props.tipoEntrega3 !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Tipo de Entrega</Label>
            <Select
              theme={selectThemeColors}
              className='react-select'
              classNamePrefix='select'
              options={comboTipoEntrega3}
              isClearable={true}
              onChange={(e) => {
                if (e) {
                  if (props.botonEnviar === undefined) {
                    props.setTipoEntrega3(e.value)
                  } else {
                    setTipoEntrega3_tmp(e.value)
                  }
                } else {
                  if (props.botonEnviar === undefined) {
                    props.setTipoEntrega3('')
                  } else {
                    setTipoEntrega3_tmp('')
                  }
                }
              }}
            />
          </Col>}
          {props.estatus !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Estatus</Label>
            <Select
              theme={selectThemeColors}
              className='react-select'
              classNamePrefix='select'
              options={comboEstatus}
              isClearable={true}
              onChange={(e) => {
                if (e) {
                  if (props.botonEnviar === undefined) {
                    props.setEstatus(e.value)
                  } else {
                    setEstatus_tmp(e.value)
                  }
                } else {
                  if (props.botonEnviar === undefined) {
                    props.setEstatus('')
                  } else {
                    setEstatus_tmp('')
                  }
                }
              }}
            />
          </Col>}
          {props.metodoEnvio !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Método de Envio</Label>
            <Select
              theme={selectThemeColors}
              className='react-select'
              classNamePrefix='select'
              options={comboMetodoEnvio}
              isClearable={true}
              onChange={(e) => {
                if (e) {
                  if (props.botonEnviar === undefined) {
                    props.setMetodoEnvio(e.value)
                  } else {
                    setMetodoEnvio_tmp(e.value)
                  }
                } else {
                  if (props.botonEnviar === undefined) {
                    props.setMetodoEnvio('')
                  } else {
                    setMetodoEnvio_tmp('')
                  }
                }
              }}
            />
          </Col>}
          {props.agrupador !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Agrupador</Label>
            <Select
              theme={selectThemeColors}
              value={agrupadorValue}
              className='react-select'
              classNamePrefix='select'
              name='filtroAgrupador'
              options={comboAgrupador}
              // isClearable={true}
              onChange={e => cambiaAgrupador(e)}
            />
          </Col>}
          {props.periodo !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Período a comparar</Label>
            {isPeriodoHidden && <LoadingGif />}
            {!isPeriodoHidden &&
            <Select
              theme={selectThemeColors}
              className='react-select'
              classNamePrefix='select'
              options={comboPeriodo}
              onChange={e => cambiaPeriodo(e)}
              value={periodoValue}
            />}
          </Col>}
          {props.formato !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Formato de Tienda</Label>
            {isFormatoHidden && <LoadingGif mini />}
            {!isFormatoHidden &&
            <Select
              theme={selectThemeColors}
              className='react-select'
              classNamePrefix='select'
              options={comboFormato}
              // isDisabled={isFormatoDisabled}
              isClearable
              onChange={e => {
                const valor = (e) ? e.value : ''
                if (props.botonEnviar === undefined) {
                  props.setFormato(valor)
                } else {
                  setFormato_tmp(valor)
                }
                setFormatoValue(e)
              }}
              value={formatoValue}
            />}
          </Col>}
          {props.canal2 !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Canal</Label>
            <Select
              theme={selectThemeColors}
              value={canal2Value}
              className='react-select'
              classNamePrefix='select'
              name='filtroCanal2'
              options={comboCanal2}
              isClearable={true}
              onChange={e => {
                if (e) {
                  setCanal2Value({label: e.label, value: e.value})
                  if (props.botonEnviar === undefined) {
                    props.setCanal2(e.value)
                  } else {
                    setCanal2_tmp(e.value)
                  }
                } else {
                  setCanal2Value({label: '', value: ''})
                  if (props.botonEnviar === undefined) {
                    props.setCanal2('')
                  } else {
                    setCanal2_tmp('')
                  }
                }
              }}
            />
          </Col>}
          {props.origen !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Origen</Label>
            <Select
              theme={selectThemeColors}
              value={origenValue}
              className='react-select'
              classNamePrefix='select'
              name='filtroOrigen'
              options={comboOrigen}
              isClearable={true}
              onChange={e => {
                if (e) {
                  setOrigenValue({label: e.label, value: e.value})
                  if (props.botonEnviar === undefined) {
                    props.setOrigen(e.value)
                  } else {
                    setOrigen_tmp(e.value)
                  }
                } else {
                  setOrigenValue({label: '', value: ''})
                  if (props.botonEnviar === undefined) {
                    props.setOrigen('')
                  } else {
                    setOrigen_tmp('')
                  }
                }
              }}
            />
          </Col>}
          {props.provLogist !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Proveedor de Logística</Label>
            <Select
              theme={selectThemeColors}
              isMulti
              value={provLogistValue}
              className="basic-multi-select"
              classNamePrefix='select'
              name='filtroProvLogist'
              options={comboProvLogist}
              isClearable={true}
              onChange={e => {
                // console.log("~~~~~~~~e:")
                // console.log(e)
                const provLogistValue_tmp = []
                const provLogistCompleto_tmp = []
                e.forEach(elemento => {
                  provLogistValue_tmp.push(elemento.value)
                  provLogistCompleto_tmp.push(elemento)
                })
                setProvLogist_tmp(provLogistValue_tmp)
                setProvLogistValue(provLogistCompleto_tmp)
              }}
            />
          </Col>}
          {props.region !== undefined  && (userData === null || userData === undefined || userData === false || userService.getNivel() >= 4) && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Región</Label>
            {isRegionHidden && <LoadingGif />}
            {!isRegionHidden &&
            <Select
              theme={selectThemeColors}
              className='react-select'
              classNamePrefix='select'
              // defaultValue={comboRegion[1]}
              options={comboRegion}
              id='region'
              isClearable
              value={regionValue}
              onChange={handleRegionChange}
            />}
          </Col>}
          {props.zona !== undefined  && (userData === null || userData === undefined || userData === false || userService.getNivel() >= 3)  && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Zona</Label>
            {isZonaHidden && <LoadingGif mini />}
            {!isZonaHidden && <Select
              theme={selectThemeColors}
              className='react-select'
              classNamePrefix='select'
              options={comboZona}
              isDisabled={isZonaDisabled}
              isClearable
              onChange={handleZonaChange}
              value={zonaValue}
            />}
          </Col>}
          {props.tienda !== undefined && (userData === null || userData === undefined || userData === false || userService.getNivel() >= 2) && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Tienda</Label>
            {isTiendaHidden && <LoadingGif mini />}
            {!isTiendaHidden && 
            <Select
              theme={selectThemeColors}
              className='react-select'
              classNamePrefix='select'
              options={comboTienda}
              isDisabled={isTiendaHidden}
              isClearable
              value={tiendaValue}
              onChange={handleTiendaChange}
            />}
          </Col>}
          {props.canal !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Canal</Label>
            {isCanalHidden && <LoadingGif />}
            {!isCanalHidden &&
            <Select
              theme={selectThemeColors}
              value={canalValue}
              className='react-select'
              classNamePrefix='select'
              defaultValue={nthElement(comboCanal, -1)}
              name='filtroCanal'
              options={comboCanal}
              isClearable={true}
              onChange={e => {
                if (e) {
                  setCanalValue({label: e.label, value: e.value})
                  if (props.botonEnviar === undefined) {
                    props.setCanal(e.value)
                  } else {
                    setCanal_tmp(e.value)
                  }
                } else {
                  setCanalValue({label: '', value: ''})
                  if (props.botonEnviar === undefined) {
                    props.setCanal('')
                  } else {
                    setCanal_tmp('')
                  }
                }
              }}
            />}
          </Col>}
          {props.grupoDeptos !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Grupo de Deptos</Label>
            <Select
              theme={selectThemeColors}
              value={grupoDeptosValue}
              className='react-select'
              classNamePrefix='select'
              name='filtroGrupoDeptos'
              options={comboGrupoDeptos}
              isClearable
              onChange={e => cambiaGrupoDeptos(e)}
            />
          </Col>}
          {props.depto !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Departamento</Label>
            {isDeptoHidden && <LoadingGif />}
            {!isDeptoHidden &&
            <Select
              theme={selectThemeColors}
              className='react-select'
              classNamePrefix='select'
              // defaultValue={comboRegion[1]}
              options={comboDepto}
              id='depto'
              isClearable
              onChange={handleDeptoChange}
            />}
          </Col>}
          {props.deptoAgrupado !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Departamento</Label>
            {isDeptoAgrupadoHidden && <LoadingGif mini />}
            {!isDeptoAgrupadoHidden &&
            <Select
              theme={selectThemeColors}
              className='react-select'
              classNamePrefix='select'
              // defaultValue={comboRegion[1]}
              options={comboDeptoAgrupado}
              value={deptoAgrupadoValue}
              isDisabled={isDeptoAgrupadoDisabled}
              id='depto'
              isClearable
              onChange={handleDeptoAgrupadoChange}
            />}
          </Col>}
          {props.subDepto !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Sub Departamento</Label>
            {isSubDeptoHidden && <LoadingGif />}
            {!isSubDeptoHidden &&
            <Select
              theme={selectThemeColors}
              className='react-select'
              classNamePrefix='select'
              options={comboSubDepto}
              isDisabled={isSubDeptoDisabled}
              isClearable
              onChange={handleSubDeptoChange}
              value={subDeptoValue}
            />}
          </Col>}
          {props.subDeptoAgrupado !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Sub Departamento</Label>
            {isSubDeptoAgrupadoHidden && <LoadingGif mini />}
            {!isSubDeptoAgrupadoHidden &&
            <Select
              theme={selectThemeColors}
              className='react-select'
              classNamePrefix='select'
              options={comboSubDeptoAgrupado}
              isDisabled={isSubDeptoAgrupadoDisabled}
              isClearable
              onChange={handleSubDeptoAgrupadoChange}
              value={subDeptoAgrupadoValue}
            />}
          </Col>}
          {props.proveedor !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Proveedor</Label>
            {isProveedorHidden && <LoadingGif />}
            {!isProveedorHidden &&
            <Select
              theme={selectThemeColors}
              className='react-select'
              classNamePrefix='select'
              defaultValue={comboProveedor[0]}
              options={comboProveedor}
              isClearable={true}
              onChange={e => {
                if (e) {
                  if (props.botonEnviar === undefined) {
                    props.setProveedor(e.value)
                  } else {
                    setProveedor_tmp(e.value)
                  }
                } else {
                  if (props.botonEnviar === undefined) {
                    props.setProveedor(0)
                  } else {
                    setProveedor_tmp(0)
                  }
                }
              }}
            />}
            <p>{props.botonEnviar === undefined ? props.proveedor : Proveedor_tmp}</p>
          </Col>}
          {props.categoria !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Categoría</Label>
            <Select
              theme={selectThemeColors}
              className='react-select'
              classNamePrefix='select'
              options={comboCategoria}
              isClearable={true}
              onChange={e => {
                if (e) {
                  if (props.botonEnviar === undefined) {
                    props.setCategoria(e.value)
                  } else {
                    setCategoria_tmp(e.value)
                  }
                } else {
                  if (props.botonEnviar === undefined) {
                    props.setCategoria('')
                  } else {
                    setCategoria_tmp('')
                  }
                }
              }}
            />
          </Col>}
          {props.tipoEntrega !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Tipo de Entrega</Label>
            <Select
              theme={selectThemeColors}
              className='react-select'
              classNamePrefix='select'
              options={comboTipoEntrega}
              isClearable={true}
              onChange={e => {
                if (e) {
                  if (props.botonEnviar === undefined) {
                    props.setTipoEntrega(e.value)
                  } else {
                    setTipoEntrega_tmp(e.value)
                  }
                } else {
                  if (props.botonEnviar === undefined) {
                    props.setTipoEntrega('')
                  } else {
                    setTipoEntrega_tmp('')
                  }
                }
              }}
            />
          </Col>}
          {props.anio !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Año</Label>
            <Select
              theme={selectThemeColors}
              value={anioValue}
              className='react-select'
              classNamePrefix='select'
              name='filtroAnio'
              options={comboAnio}
              isClearable={false}
              onChange={e => {
                setAnioValue({label: e.label, value: e.value})
                if (props.botonEnviar === undefined) {
                  props.setAnio(e.value)
                } else {
                  setAnio_tmp(e.value)
                }
                setFecha_fin_tmp(new Date(`${e.value}-${mesValue.value}-${fechas_srv.ultimoDiaVencidoDelMesReal(e.value, mesValue.value)}`))
              }}
            />
          </Col>}
          {props.anioOpcional !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Año</Label>
            <Select
              theme={selectThemeColors}
              value={anioOpcionalValue}
              className='react-select'
              classNamePrefix='select'
              name='filtroAnio'
              options={comboAnioOpcional}
              isClearable={true}
              onChange={e => {
                const label = (e) ? e.label : ''
                const value = (e) ? e.value : 0
                setAnioOpcionalValue({label, value})
                if (props.botonEnviar === undefined) {
                  props.setAnioOpcional(value)
                } else {
                  setAnioOpcional_tmp(value)
                }
              }}
            />
          </Col>}
          {props.mes !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Mes</Label>
            <Select
              theme={selectThemeColors}
              value={mesValue}
              className='react-select'
              classNamePrefix='select'
              options={comboMes}
              isClearable={false}
              onChange={e => {
                setMesValue({label: e.label, value: e.value})
                if (props.botonEnviar === undefined) {
                  props.setMes(e.value)
                } else {
                  setMes_tmp(e.value)
                }
                const mes = (e.value < 10) ? `0${e.value + 1}` : `${e.value + 1}`
                setFecha_fin_tmp(new Date(`${anioValue.value}-${mes}-${fechas_srv.ultimoDiaVencidoDelMesReal(anioValue.value, mes)}`))
              }}
            />
          </Col>}
          {props.mesOpcional !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Mes</Label>
            <Select
              theme={selectThemeColors}
              value={mesOpcionalValue}
              className='react-select'
              classNamePrefix='select'
              options={comboMesOpcional}
              isClearable={true}
              onChange={e => {
                const label = (e) ? e.label : ''
                const value = (e) ? e.value : 0
                setMesOpcionalValue({label, value})
                if (props.botonEnviar === undefined) {
                  props.setMesOpcional(value)
                } else {
                  setMesOpcional_tmp(value)
                }
                const mes = (value < 10) ? `0${value + 1}` : `${value + 1}`
              }}
            />
          </Col>}
          {props.anioRFM !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Año</Label>
            <Select
              theme={selectThemeColors}
              value={anioValueRFM}
              className='react-select'
              classNamePrefix='select'
              name='filtroAnioRFM'
              options={comboAnioRFM}
              isClearable={false}
              onChange={e => {
                setAnioValueRFM({label: e.label, value: e.value})
                if (props.botonEnviar === undefined) {
                  props.setAnioRFM(e.value)
                } else {
                  setAnio_tmp(e.value)
                }
              }}
            />
          </Col>}
          {props.mesRFM !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Último mes del trimestre</Label>
            <Select
              theme={selectThemeColors}
              value={mesValueRFM}
              className='react-select'
              classNamePrefix='select'
              options={comboMesRFM}
              isClearable={false}
              onChange={e => {
                setMesValueRFM({label: e.label, value: e.value})
                if (props.botonEnviar === undefined) {
                  props.setMesRFM(e.value)
                } else {
                  setMesRFM_tmp(e.value)
                }
              }}
            />
          </Col>}
          {props.nps !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>Categoría NPS</Label>
            {isNpsHidden && <LoadingGif mini />}
            {!isNpsHidden &&
            <Select
              theme={selectThemeColors}
              className='react-select'
              classNamePrefix='select'
              options={comboNps}
              // isDisabled={isFormatoDisabled}
              isClearable
              onChange={e => {
                const valor = (e) ? e.value : ''
                setNpsValue(e)
                if (props.botonEnviar === undefined) {
                  props.setNps(valor)
                } else {
                  setNps_tmp(valor)
                }
              }}
              value={npsValue}
            />}
          </Col>}
          {props.e3 !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
            <Label>E3</Label>
            <Select
              theme={selectThemeColors}
              value={e3Value}
              className='react-select'
              classNamePrefix='select'
              name='filtroE3'
              options={comboE3}
              isClearable={true}
              onChange={e => {
                if (e) {
                  setE3Value({label: e.label, value: e.value})
                  if (props.botonEnviar === undefined) {
                    props.setE3(e.value)
                  } else {
                    setE3_tmp(e.value)
                  }
                } else {
                  setE3Value({label: '', value: ''})
                  if (props.botonEnviar === undefined) {
                    props.setE3('')
                  } else {
                    setE3_tmp('')
                  }
                }
              }}
            />
          </Col>}
          {props.botonEnviar !== undefined && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs} style={{marginTop: '23px'}}>
          {bloqueadoBotonEnviar && <LoadingGif mini />}
          {!bloqueadoBotonEnviar &&
          <Button
            color='primary'
            // disabled={bloqueadoBotonEnviar}
            className='botonEnviar'
            onClick={async (e) => {
              props.setBotonEnviar(props.botonEnviar + 1)
              for (const [key, value] of Object.entries(props)) {
                if (key.substr(0, 3) === 'set') {
                  const getter = key.slice(3)
                  if (getter !== 'BotonEnviar') {
                    if (getter === 'Fechas' && props.fechas.fecha_ini === '') {
                      props.setFechas({fecha_ini: '', fecha_fin: fecha_fin_tmp})
                    } else if (getter === 'Fechas' && props.fechas.fecha_fin === '') {
                      props.setFechas({fecha_ini: fecha_ini_tmp, fecha_fin: ''})
                    } else {
                      eval(`props[key](${getter}_tmp)`)
                    }
                  }
                }
              }
            }}
          >
            <img src={Lupita} />
          </Button>}

          </Col>}
          {bootstrap.espacio && <Col className='mb-1' xl={bootstrap.xl} lg={bootstrap.lg} sm={bootstrap.sm} xs={bootstrap.xs}>
          </Col>}
        </Row>
        {/* <Row className='match-height'>
          <Col>&nbsp;</Col>
        </Row> */}
    </>
  )
}
export default Filtro
