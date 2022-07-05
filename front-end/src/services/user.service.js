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

  registro(apellidoM, apellidoP, email, nombre, password1, areas, tienda, nivel) {
    return axios({
      method: 'post',
      url: `${CustomUrls.ApiUrl()}registro`,
      headers: {
        accept:'application/json',
        'Content-Type':'application/json'
      },
      data: {
        apellidoM, 
        apellidoP, 
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
  getTienda() {
    const userData = JSON.parse(localStorage.getItem('userData'))
    return userData["tienda"]
  }
  getRegion() {
    const userData = JSON.parse(localStorage.getItem('userData'))
    return userData["region"]
  }
  getZona() {
    const userData = JSON.parse(localStorage.getItem('userData'))
    return userData["zona"]
  }
  getLugarNombre() {
    const userData = JSON.parse(localStorage.getItem('userData'))
    return userData["lugarNombre"]
  }
  getEmail() {
    const userData = JSON.parse(localStorage.getItem('userData'))
    return userData["usuario"]
  }
}

export default new UserService()
