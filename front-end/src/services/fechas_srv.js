class fechas_srv {
    primeroDelMesVencido(anio = false, mes = false) {
        const hoy = new Date()
        mes = (mes) ? mes : hoy.getMonth()
        anio = (anio) ? anio : hoy.getFullYear()
        const dia = hoy.getDate()
        if (dia !== 1) {
            return new Date(anio, mes, 1)
        } else {
            if (mes !== 0) {
                return new Date(anio, mes - 1, 1)
            } else {
                return new Date(anio - 1, 11, 1)
            }
        }
    }
    primeroDelMesSinVencer(anio = false, mes = false) {
        const hoy = new Date()
        mes = (mes) ? mes : hoy.getMonth()
        anio = (anio) ? anio : hoy.getFullYear()
        return new Date(anio, mes, 1)
    }
    actualVencida() {
        const hoy = new Date()
        const dia = hoy.getDate()
        const mes = hoy.getMonth()
        const anio = hoy.getFullYear()
        // if (dia !== 1) {
        if (dia !== 1) {
            return new Date(anio, mes, dia - 1) // Si el día es 1, al quedar en 0 regresa el último día del mesa anterior
        } else {
            if (mes !== 0) {
                return new Date(anio, mes - 1, new Date(anio, mes, 0).getDate())
            } else {
                return new Date(anio - 1, 11, 31)
            }
        }
    }
    primeraDelAnio(anio = false) { // Si hoy es enero, regresa el primer día del año anterior
        const hoy = new Date()
        const dia = hoy.getDate()
        const mes = hoy.getMonth()
        anio = (anio) ? anio : hoy.getFullYear()
        if (mes !== 0) {
            return new Date(anio, 0, 1)
        } else {
            return new Date(anio - 1, 0, 1)
        }
    }
    ultimaDelAnio(anio = false) { // Si hoy es enero, regresa el último día del año anterior
        const hoy = new Date()
        const dia = hoy.getDate()
        const mes = hoy.getMonth()
        anio = (anio) ? anio : hoy.getFullYear()
        if (anio === hoy.getFullYear() && mes !== 0) {
            return new Date(anio, mes, dia)
        } else {
            return new Date(anio, 11, 31)
        }        
    }
    anioActual() {
        const hoy = new Date()
        return hoy.getFullYear()
    }
    mesTexto(mes = undefined, base0 = true) {
        const hoy = new Date()
        const mes_elegido = (mes !== undefined) ? mes : hoy.getMonth()
        const meses_txt = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        return (base0) ? meses_txt[mes_elegido] : meses_txt[mes_elegido - 1]
    }
    diaActual() {
        const hoy = new Date()
        return hoy.getDate()
    }
    mesActual() {
        const hoy = new Date()
        return hoy.getMonth()
    }
    diaActualOUltimoDelMes(anio = false, mes = false) {
        const hoy = new Date()
        // console.log(`HOY: ${hoy}`)
        if (anio === hoy.getFullYear() && mes === hoy.getMonth()) {
            // console.log(`Día del mes de hoy: ${hoy.getDate()}`)
            return hoy.getDate()
        } else {
            return new Date(anio, mes + 1, 0).getDate()
        }
    }
    ultimoMesVencidoReal(anio) {
        const hoy = new Date()
        if (anio === hoy.getFullYear() || anio === undefined) {
            if (hoy.getDate() !== 1) {
                return hoy.getMonth()
            } else if (hoy.getMonth() !== 0) {
                return hoy.getMonth() - 1
            } else {
                return 11
            }
        } else {
            return 11
        }
    }
    ultimoDiaVencidoDelMesReal(anio, mes) {
        const hoy = new Date()
        if ((anio === hoy.getFullYear() && mes === hoy.getMonth()) || mes === undefined) {
            if (hoy.getDate() !== 1) {
                return hoy.getDate() - 1
            } else {
                return new Date(anio, mes, 0).getDate()
            }
            
        } else {
            return new Date(anio, mes + 1, 0).getDate()
        }
    }
    ultimoDiaSinVencerDelMesReal(anio, mes) {
        const hoy = new Date()
        if ((anio === hoy.getFullYear() && mes === hoy.getMonth()) || anio === undefined) {
            return hoy.getDate()
        } else {
            return new Date(anio, mes + 1, 0).getDate()
        }
    }
    tresMesesMenos(anio, mes) {
        if (mes < 3) {
            return `${this.mesTexto(10 + mes, false)} ${anio - 1}`
        } else {
            return `${this.mesTexto(mes - 2, false)} ${anio}`
        }
    }
    noUTC(fecha) {
        // console.log("entramos a fechas_srv -> noUtc")
        const offset = fecha.getTimezoneOffset()
        // console.log(`Offset: ${offset}`)
        return new Date(fecha.getTime() - (offset * 60000))
        // return fecha
    }
    hoy_fin() {
        const endOfDay = new Date()
        endOfDay.setUTCHours(23, 59, 59, 999)
        return endOfDay
    }
}
  
export default new fechas_srv()