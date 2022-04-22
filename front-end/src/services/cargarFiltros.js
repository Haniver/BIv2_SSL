import axios from 'axios'
import authHeader from '@src/services/auth.header'
import CustomUrls from './customUrls'

class CargarFiltros {
    cargarRegion = async () => {
        return axios({
            method: 'get',
            url: `${CustomUrls.ApiUrl()}filtros/cargarRegion`
        })
        .then(resp => {
            return resp.data
            // console.log(resp)
        })
    }

    cargarZona = async (region) => {
        return axios({
            method: 'get',
            url: `${CustomUrls.ApiUrl()}filtros/cargarZona?region=${region}`
        })
        .then(resp => {
            return resp.data
            // console.log(resp)
        })
    }

    cargarTienda = async (zona) => {
        return axios({
            method: 'get',
            url: `${CustomUrls.ApiUrl()}filtros/cargarTienda?zona=${zona}`
        })
        .then(resp => {
            return resp.data
            // console.log(resp)
        })
    }

    cargarProveedor = async () => {
        return axios({
            method: 'get',
            url: `${CustomUrls.ApiUrl()}filtros/cargarProveedor`,
            headers: authHeader()
        })
        .then(resp => {
            return resp.data
            // console.log(resp)
        })
    }

    cargarDepto = async () => {
        return axios({
            method: 'get',
            url: `${CustomUrls.ApiUrl()}filtros/cargarDepto`,
            headers: authHeader()
        })
        .then(resp => {
            return resp.data
            // console.log(resp)
        })
    }

    cargarSubDepto = async (depto) => {
        return axios({
            method: 'get',
            url: `${CustomUrls.ApiUrl()}filtros/cargarSubDepto?depto=${depto}`,
            headers: authHeader()
        })
        .then(resp => {
            return resp.data
            // console.log(resp)
        })
    }

    cargarPeriodo = async (agrupador, fechas) => {
        return axios({
            method: 'post',
            url: `${CustomUrls.ApiUrl()}filtros/cargarPeriodo`,
            headers: authHeader(),
            data: {
              agrupador,
              fechas
            }
  
        })
        .then(resp => {
            return resp.data
            // console.log(resp)
        })
    }

    cargarFormato = async () => {
        return axios({
            method: 'get',
            url: `${CustomUrls.ApiUrl()}filtros/cargarFormato`,
            headers: authHeader()
        })
        .then(resp => {
            return resp.data
            // console.log(resp)
        })
    }

    cargarNps = async () => {
        return axios({
            method: 'get',
            url: `${CustomUrls.ApiUrl()}filtros/cargarNps`,
            headers: authHeader()
        })
        .then(resp => {
            return resp.data
            // console.log(resp)
        })
    }
    nombreTienda(idTienda) {
        return axios({
            method: 'get',
            url: `${CustomUrls.ApiUrl()}filtros/nombreTienda?tienda=${idTienda}`,
            headers: authHeader()
        })
    }

    cargarDeptoAgrupado = async (grupoDeptos) => {
        return axios({
            method: 'get',
            url: `${CustomUrls.ApiUrl()}filtros/cargarDeptoAgrupado?grupoDeptos=${grupoDeptos}`,
            headers: authHeader()
        })
        .then(resp => {
            return resp.data
            // console.log(resp)
        })
    }

    cargarSubDeptoAgrupado = async (deptoAgrupado) => {
        return axios({
            method: 'get',
            url: `${CustomUrls.ApiUrl()}filtros/cargarSubDeptoAgrupado?deptoAgrupado=${deptoAgrupado}`,
            headers: authHeader()
        })
        .then(resp => {
            return resp.data
            // console.log(resp)
        })
    }

}

export default new CargarFiltros()
