import axios from 'axios'
import CustomUrls from './customUrls'
import authHeader from './auth.header'
// import authHeader from '@src/services/auth.header'

class UserService {
  recuperarPassword(email) {
    return axios({
      method: 'post',
      url: `${CustomUrls.ApiUrl()}recuperarPassword`,
      headers: {
        accept: 'application/json',
        'Content-Type':'application/json'
      }, 
      data: {
        usuario: email // This is the body part
      }
    })
  }

  cambiarPasswordActivo(token) {
    return axios.get(`${CustomUrls.ApiUrl()}cambiarPasswordActivo/${token}`)
  }

  cambiarPassword(password, token) {
    return axios({
      method: 'post',
      url: `${CustomUrls.ApiUrl()}cambiarPassword`,
      headers: {
        accept:'application/json',
        'Content-Type':'application/json'
      }, 
      data: {
        password, // This is the body part
        token
      }
    })
  }

  cambiarPerfil(passwordVieja, password, tienda) {
    return axios({
      method: 'post',
      url: `${CustomUrls.ApiUrl()}cambiarPerfil`,
      headers: authHeader(),
      data: {
        passwordVieja,
        password,
        tienda
      }
    })
  }

  verificarUsuario(usuario) {
    return axios({
      method: 'post',
      url: `${CustomUrls.ApiUrl()}verificarUsuario`,
      headers: {
        accept:'application/json',
        'Content-Type':'application/json'
      },
      data: {
        usuario
      }
    })
  }

  // roles() {
  //   return axios.get(`${CustomUrls.ApiUrl()}roles/`)
  // }

  areas() {
    return axios.get(`${CustomUrls.ApiUrl()}areas/`)
  }

  async todasLasTiendas() {
    return axios.get(`${CustomUrls.ApiUrl()}todasLasTiendas/`)
  }

  registro(email, nombre, password1, areas, tienda, nivel) {
    return axios({
      method: 'post',
      url: `${CustomUrls.ApiUrl()}registro`,
      headers: {
        accept:'application/json',
        'Content-Type':'application/json'
      },
      data: {
        usuario: email, 
        nombre, 
        password: password1, 
        areas, 
        tienda, 
        nivel
      }
    })
  }

  cargarMenu(vistasPermitidas) {
    return axios({
      method: 'post',
      url: `${CustomUrls.ApiUrl()}cargarMenu`,
      headers: {
        accept:'application/json',
        'Content-Type':'application/json'
      },
      data: {
        vistasPermitidas
      }
    })
  }

  getNivel() {
    const userData = JSON.parse(localStorage.getItem('userData'))
    return userData["nivel"]
  }
  getRegion() {
    const userData = JSON.parse(localStorage.getItem('userData'))
    if (userData["region"] !== undefined && userData["region"]) {
      return userData["region"]
    } else {
      return ''
    }
  }
  getZona() {
    const userData = JSON.parse(localStorage.getItem('userData'))
    if (userData["zona"] !== undefined && userData["zona"]) {
      return userData["zona"]
    } else {
      return ''
    }
  }
  getTienda() {
    const userData = JSON.parse(localStorage.getItem('userData'))
    if (userData["tienda"] !== undefined && userData["tienda"]) {
      return userData["tienda"]
    } else {
      return ''
    }
  }
  getRegionPorNivel() {
    const userData = JSON.parse(localStorage.getItem('userData'))
    if (userData["region"] !== undefined && userData["region"] && Number(this.getNivel()) <= 3) {
      return userData["region"]
    } else {
      return ''
    }
  }
  getZonaPorNivel() {
    const userData = JSON.parse(localStorage.getItem('userData'))
    if (userData["zona"] !== undefined && userData["zona"] && Number(this.getNivel()) <= 2) {
      return userData["zona"]
    } else {
      return ''
    }
  }
  getTiendaPorNivel() {
    const userData = JSON.parse(localStorage.getItem('userData'))
    if (userData["tienda"] !== undefined && userData["tienda"] && Number(this.getNivel()) === 1) {
      return userData["tienda"]
    } else {
      return ''
    }
  }
  getLugarNombre() {
    const userData = JSON.parse(localStorage.getItem('userData'))
    return userData["lugarNombre"]
  }
  getEmail() {
    const userData = JSON.parse(localStorage.getItem('userData'))
    return userData["usuario"]
  }
  async getIdFromEmail(email) {
    return axios({
      method: 'get',
      url: `${CustomUrls.ApiUrl()}getIdFromEmail?email=${email}`,
      headers: authHeader()
    })
    .then(resp => {
      return resp.data
      // console.log(resp)
    })
  }
  updateUsuario (email, nombre, areas, tienda, nivel, estatus, razonRechazo, id) {
    return axios({
      method: 'post',
      url: `${CustomUrls.ApiUrl()}updateUsuario`,
      headers: {
        accept:'application/json',
        'Content-Type':'application/json'
      },
      data: {
        usuario: email, 
        nombre, 
        areas, 
        tienda, 
        nivel, 
        estatus, 
        razonRechazo,
        id,
        password: ''
      }
    })
  }

}

export default new UserService()
