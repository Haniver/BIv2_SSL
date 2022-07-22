from datetime import date, datetime, timedelta
import calendar

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

def ultimoDiaVencidoDelMesReal(anio = date.today().year, mes = date.today().month):
    hoy = date.today()
    if hoy.day != 1:
        return hoy.day - 1
    else:
        if mes != 1:
            return calendar.monthrange(anio, mes - 1)[1]
        else:
            return 31
