import { useState } from 'react'

const useBloques = async (Highcharts) => {
  const [bloques, setBloques] = useState([{ highcharts: Highcharts, options: {}, laterales: [] }])

  const updateBloques = (opciones_fila, laterales_tmp) => {
    setBloques([...bloques, { highcharts: Highcharts, options: opciones_fila, laterales: laterales_tmp }])
  }

  return [bloques, updateBloques]
}

export default useBloques
