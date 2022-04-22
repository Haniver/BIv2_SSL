meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

def fechaAbrevEspanol(fecha):
    dia = str(fecha.day)
    mes = meses[fecha.month-1]
    return dia + ' ' + mes

def ddmmyyyy(fecha):
    dia = str(fecha.day) if fecha.day >= 10 else '0' + str(fecha.day)
    mes = str(fecha.month) if fecha.month >= 10 else '0' + str(fecha.month)
    anio = str(fecha.year)
    return dia + '/' + mes + '/' + anio

def mesTexto(mes):
    return meses[mes - 1]
