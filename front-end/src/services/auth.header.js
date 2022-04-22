import Cookies from 'js-cookie'

export default function authHeader() {
  // const user = JSON.parse(localStorage.getItem('user')); // No vas a usar esto porque no necesitas obtener toda la información del usuario del almacenamiento local para saber el token; ese lo sacas de las cookies

  let jwt = Cookies.get('tokenHeaderPayload') + Cookies.get('tokenSignature')
  jwt = jwt.slice(1, -1)
  // if (user && user.accessToken) { // Lo mismo que arriba
  if (jwt) {
    return { Authorization: `Bearer ${jwt}` } // for Spring Boot back-end
  } else {
    return {}
  }
}
