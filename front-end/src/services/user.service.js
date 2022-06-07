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

  yaExisteUsuario(usuario) {
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

  roles() {
    return axios.get(`${CustomUrls.ApiUrl()}roles/`)
  }

  registro(apellidoM, apellidoP, usuario, nombre, password, id_rol, tienda) {
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
        usuario,
        nombre,
        password,
        id_rol,
        tienda
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
}

export default new UserService()
