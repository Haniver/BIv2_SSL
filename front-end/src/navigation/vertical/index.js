import { Truck, Home, BarChart2, Search, Clock, DollarSign, FileMinus, Award, Monitor, Grid, MapPin, Watch, Sunrise, Volume2, CornerLeftDown, Box, ShoppingBag, Rewind, RotateCw, Tool, UserPlus, Map, HelpCircle, Database, Code, FileText } from 'react-feather'

const dashboards = []
const reportes = []
const herramientas = []
const docsTutorial = []
const docsCodigo = []
const docsBD = []
const documentos = []
const navigation = [
  {
    id: 'dashboards',
    title: 'Dashboards',
    icon: <BarChart2 size={30} />,
    badge: 'light-warning',
    children: dashboards
  }
]
  const userData = JSON.parse(localStorage.getItem('userData'))
  if (userData !== null) {
    // console.log(userData["vistas"])
    const vistas = JSON.parse(userData["vistas"])
    const documentos_api = JSON.parse(userData["documentos"])
    // console.log('vistas:')
    // console.log(vistas)
    if (vistas !== undefined) {
      const iconos = {
        Truck, 
        Home, 
        BarChart2, 
        Search, 
        Clock, 
        DollarSign, 
        FileMinus, 
        Award, 
        Monitor, 
        Grid, 
        MapPin, 
        Watch, 
        Sunrise, 
        Volume2, 
        CornerLeftDown, 
        Box, 
        ShoppingBag, 
        Rewind, 
        RotateCw,
        Tool,
        UserPlus,
        Map,
        HelpCircle,
        Database,
        Code,
        FileText
      }

      vistas.forEach(elemento => {
        const Icono = iconos[elemento.icon]
        const objeto_a_insertar = {
          id: elemento.idReact,
          id_vista: elemento.id_vista,
          title: elemento.title,
          icon: <Icono size={30} />,
          navLink: `/${elemento.idReact}`
        }
        if (elemento.categoria === 'Dashboard') {
          dashboards.push(objeto_a_insertar)
        } else if (elemento.categoria === 'Reporte') {
          reportes.push(objeto_a_insertar)
        } else if (elemento.categoria === 'Herramientas') {
          herramientas.push(objeto_a_insertar)
        }
      })
      documentos_api.forEach(elemento => {
        const Icono = iconos[elemento.icon]
        const objeto_a_insertar = {
          id: elemento.nombre_archivo,
          title: elemento.title,
          icon: <Icono size={30} />,
          navLink: `/documentos/${elemento.nombre_archivo}`
        }
        if (elemento.categoria === 'Tutorial') {
          docsTutorial.push(objeto_a_insertar)
        } else if (elemento.categoria === 'Codigo') {
          docsCodigo.push(objeto_a_insertar)
        } else if (elemento.categoria === 'BD') {
          docsBD.push(objeto_a_insertar)
        }
      })
      if (reportes.length > 0) {
        navigation.push(
          {
            id: 'reportes',
            title: 'Reportes',
            icon: <Grid size={30} />,
            badge: 'light-warning',
            children: reportes
          }
        )
      }
      if (herramientas.length > 0) {
        navigation.push(
          {
            id: 'herramientas',
            title: 'Herramientas',
            icon: <Tool size={30} />,
            badge: 'light-warning',
            children: herramientas
          }
        )
      }
      if (docsTutorial.length > 0) {
        documentos.push(
          {
            id: 'tutorial',
            title: 'Tutorial',
            icon: <HelpCircle size={30} />,
            badge: 'light-warning',
            children: docsTutorial
          }
        )
      }
      if (docsBD.length > 0) {
        documentos.push(
          {
            id: 'bd',
            title: 'Base de Datos',
            icon: <Database size={30} />,
            badge: 'light-warning',
            children: docsBD
          }
        )
      }
      if (docsCodigo.length > 0) {
        documentos.push(
          {
            id: 'codigo',
            title: 'Código',
            icon: <Code size={30} />,
            badge: 'light-warning',
            children: docsCodigo
          }
        )
      }
      if (documentos.length > 0) {
        navigation.push(
          {
            id: 'documentos',
            title: 'Documentos',
            icon: <FileText size={30} />,
            badge: 'light-warning',
            children: documentos
          }
        )
      }
    }
  }

  console.log('navigation:')
  console.log(navigation)
  export default navigation