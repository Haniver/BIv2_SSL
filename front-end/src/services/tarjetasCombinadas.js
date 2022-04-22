import axios from 'axios'
import CustomUrls from './customUrls'
import authHeader from './auth.header'

async function tarjetasCombinadas(seccion, titulo, props) {
// function llamadaAPI(seccion, props) {
    // console.log("Se va a mandar llamar axios desde tarjetasCombinads.js")
    const res = await axios({
        method: 'post',
        url: `${CustomUrls.ApiUrl()}tarjetasCombinadas/${seccion}?titulo=${titulo}`,
        headers: authHeader(),
        data: props
    })
    return res.data
}

export default tarjetasCombinadas