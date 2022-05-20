export function nthElement (arr, n = 0) {
    return (n > 0 ? arr.slice(n, n + 1) : arr.slice(n))[0]
}

export function procesarSerie(arreglo, formato) {
    if (formato === 'entero' || formato === 'texto') {
        return arreglo
    } else {
        const resultado = []
        arreglo.forEach(num => {
            // console.log(`num al inicio: ${num} y formato=${formato}`)
            if (formato === 'porcentaje' || formato === 'multiple') {
                num *= 100
            }
            const m = Number((Math.abs(num) * 100).toPrecision(15))
            num = Math.round(m) / 100 * Math.sign(num)
            resultado.push(num)
            // console.log(`num al final: ${num}`)
        })
        // console.log("Y resultado:")
        // console.log(resultado)
        return resultado
    }
}