import { useState } from 'react'

const updateBloques = async (opcionesFila, lateralesTmp) => {
  setBloques(prevBloques => [
    ...prevBloques,
    {
      highcharts: Highcharts,
      options: opcionesFila,
      laterales: lateralesTmp,
    },
  ])
}

export default updateBloques
