import smtplib
from email.mime.text import MIMEText
from email.header import Header
import servicios.credenciales as credenciales

def enviarEmail(titulo, receivers, cuerpo):
    sender = credenciales.mail()['email']
    message = MIMEText(cuerpo, 'html', 'utf-8')
    message['Subject'] = Header(titulo, 'utf-8')
    message['From'] = Header('Reportes Omnicanal', 'utf-8')
    
    mailserver = smtplib.SMTP('smtp.office365.com',587)
    mailserver.ehlo()
    mailserver.starttls()
    mailserver.login(credenciales.mail()['usuario'], credenciales.mail()['password'])
    try:
        mailserver.sendmail(sender, receivers, message.as_string())
        mailserver.quit()
        return {'mensaje':'Email enviado con éxito'}
    except smtplib.SMTPException:
        mailserver.quit()
        return {'mensaje':'Error al enviar email'}
    