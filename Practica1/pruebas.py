import time
from pysnmp.hlapi import *

def consultaSNMP(comunidad,host,puerto,oid):
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
               CommunityData(comunidad),
               UdpTransportTarget((host, int(puerto))),
               ContextData(),
               ObjectType(ObjectIdentity(oid))))

    if errorIndication:
        resultado = errorIndication 
    elif errorStatus:
        print('%s at %s' % (errorStatus.prettyPrint(),errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
    else:
        for varBind in varBinds:
            varB=(' = '.join([x.prettyPrint() for x in varBind]))
            resultado= varB.split()[2]
    return resultado

host = "192.168.100.10"
version = "1"
comunidad = "comunidadSNMP"
puerto = 161

while(True):
    consultaSNMP(comunidad,host,puerto,'1.3.6.1.2.1.2.2.1.11.1')
    time.sleep(1)

#guardardispositivo(nombre,host,version,comunidad,puerto)