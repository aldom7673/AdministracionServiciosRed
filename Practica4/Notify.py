import smtplib
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

COMMASPACE = ', '
# Define params
pngpath = 'Monitoreo/'

mailsender = "aldom7673@gmail.com"
mailreceip = "tanibet.escom@gmail.com"
mailserver = 'smtp.gmail.com: 587'
password = 'blink_149'

def send_alert_attached(subject, imagen):
    """ Will send e-mail, attaching png
    files in the flist.
    """
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = mailsender
    msg['To'] = mailreceip
    fp = open(pngpath + imagen + '.png', 'rb')
    img = MIMEImage(fp.read())
    fp.close()
    texto = MIMEText("El umbral ha sido superado, por favor, implemente las acciones correspondientes para atender el problema.")
    msg.attach(img)
    msg.attach(texto)
    mserver = smtplib.SMTP(mailserver)
    mserver.starttls()
    # Login Credentials for sending the mail
    mserver.login(mailsender, password)

    mserver.sendmail(mailsender, mailreceip, msg.as_string())
    mserver.quit()