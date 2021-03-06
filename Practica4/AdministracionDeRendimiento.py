import getpass
import ftplib
import telnetlib
import os
import threading
import time
import rrdtool
import datetime
from Notify import send_alert_attached
from datetime import timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from getSNMP import consultaSNMP, consultaSNMPWalk
from reportlab.lib.utils import ImageReader

IP = 0
VERSION_SNMP = 1
COMUNIDAD = 2
PUERTO = 3
ID = 4
UMBRAL_READY_RAM = '25'
UMBRAL_SET_RAM = '40'
UMBRAL_GO_RAM = '90'

UMBRAL_READY_CPU = '20'
UMBRAL_SET_CPU = '40'
UMBRAL_GO_CPU = '60'

UMBRAL_READY_STORAGE = '20'
UMBRAL_SET_STORAGE = '40'
UMBRAL_GO_STORAGE = '70'

BANDERA_CORREO_READY = False
BANDERA_CORREO_SET = False
BANDERA_CORREO_GO = False

def InicializarVariables():
    #print( "Cargando datos de los agentes" )
    try:
        archivoAgentes = open ( "AgentesRegistrados.txt", "r" )
        for agente in archivoAgentes:
            datosAgente = agente.split( ', ' )
            ip = datosAgente[IP]
            comunidad = datosAgente[COMUNIDAD]
            ultimoID = datosAgente[ID].split( '\n' )[0]
            agentes.append( ip )
            thread_read = threading.Thread(target = MonitorearAgente, args=[ip, comunidad, ultimoID])
            thread_read.start()
    except:
        archivoAgentes = open( "AgentesRegistrados.txt", "w" )
        agente = "127.0.0.1, v1, comunidadSNMP, 161, 0\n"
        agentes.append("127.0.0.1")
        ultimoID = '0'
        thread_read = threading.Thread(target = MonitorearAgente, args=["127.0.0.1", "comunidadSNMP",ultimoID])
        thread_read.start()
        archivoAgentes.write(agente)
    archivoAgentes.close()
    return ultimoID

def MonitorearRendimientoAgente(ip, comunidad, idAgente):
    RAMLoad = StorageLoad = 0.0
    numeroRam = numeroAlamacenamiento = CPULoads = ''
    CPUs= []
    RRA = []
    DS = []

    while(ip in agentes):
        estadoDelAgente = str(consultaSNMP( comunidad, ip, '1.3.6.1.2.1.1.1.0'))

        if( estadoDelAgente.split( )[0] != "No" ):
            if(len(DS) == 0 and len(RRA) == 0):
                CPUs =  consultaSNMPWalk(comunidad, ip, '1.3.6.1.2.1.25.3.3.1.2')
                DS.append("DS:RAM:GAUGE:600:U:U")
                RRA.append("RRA:AVERAGE:0.5:1:60")
                DS.append("DS:Storage:GAUGE:600:U:U")
                RRA.append("RRA:AVERAGE:0.5:1:60")
                for cpu in CPUs:
                    DS.append("DS:CPU" + cpu +":GAUGE:600:U:U")
                    RRA.append("RRA:AVERAGE:0.5:1:60")
                crearRRDsMonitoreo(idAgente,DS,RRA)

            if( numeroAlamacenamiento == '' ):
                consultaSistemaOperativo = str(consultaSNMP(comunidad, ip, '1.3.6.1.2.1.1.1.0'))

            entidad = "Physical Memory" #Memoria RAM
            if( numeroRam == ''):
                numeroRam = consultaSNMPWalk(comunidad, ip,'1.3.6.1.2.1.25.2.3.1.3', entidad)
            TotalRAM = consultaSNMP(comunidad, ip, '1.3.6.1.2.1.25.2.3.1.5.' + numeroRam)
            UsoRAM = consultaSNMP(comunidad, ip, '1.3.6.1.2.1.25.2.3.1.6.' + numeroRam)
            RAMLoad = str(int(UsoRAM) * 100 / int( TotalRAM ))

            if( numeroAlamacenamiento == ''):
                if (consultaSistemaOperativo == 'Linux'):
                    entidad = "/" #Almacenamiento
                else:
                    entidad = "c:" #Almacenamiento
                numeroAlamacenamiento = consultaSNMPWalk(comunidad, ip,'1.3.6.1.2.1.25.2.3.1.3', entidad, consultaSistemaOperativo != 'Linux')
            TotalStorage = consultaSNMP(comunidad, ip, '1.3.6.1.2.1.25.2.3.1.5.' + numeroAlamacenamiento)
            UsoStorage = consultaSNMP(comunidad, ip, '1.3.6.1.2.1.25.2.3.1.6.' + numeroAlamacenamiento)
            StorageLoad = str(int(UsoStorage) * 100 / int(TotalStorage))
            
            if(len(CPUs) == 0):
                CPUs =  consultaSNMPWalk(comunidad, ip, '1.3.6.1.2.1.25.3.3.1.2')

            CPULoads = ''
            for cpu in CPUs:
                if( cpu != CPUs[len(CPUs) - 1] ):
                    CPULoads += consultaSNMP(comunidad, ip, '1.3.6.1.2.1.25.3.3.1.2.' + cpu)+":"
                else:
                    CPULoads += consultaSNMP(comunidad, ip, '1.3.6.1.2.1.25.3.3.1.2.' + cpu)
            
            valor =  "N:" + RAMLoad + ':' + StorageLoad + ':' + CPULoads            
            rrdtool.update("RRDsAgentes/monitoreo" + idAgente + '.rrd', valor)
            rrdtool.dump('RRDsAgentes/monitoreo' + idAgente + '.rrd','RRDsAgentes/monitoreo' + idAgente + '.xml')
            print(CPULoads)
            MonitorearComportamiento(idAgente, comunidad, ip)
            time.sleep(3)
            
def MonitorearAgente(ip, comunidad, idAgente):
    crearRRDs(idAgente)
    print("Monitoreando agente ", ip)
    thread_read = threading.Thread(target = MonitorearRendimientoAgente, args=[ip, comunidad, idAgente])
    thread_read.start()
    while(ip in agentes):
        ifInUcastPkts = ipInReceives = icmpOutEchos = tcpInSegs = udpInDatagrams = "0"
        estadoDelAgente = str(consultaSNMP( comunidad, ip, '1.3.6.1.2.1.1.1.0'))
        if( estadoDelAgente.split( )[0] != "No" ):
            #print( "1. Paquetes unicast que ha recibido 1.3.6.1.2.1.2.2.1.11.X" )
            paquetesUnicast = consultaSNMP( comunidad, ip, '1.3.6.1.2.1.2.2.1.11.1' )        
            ifInUcastPkts = str(paquetesUnicast) if str(paquetesUnicast).isdigit() else ifInUcastPkts      

            #print( "2. Paquetes recibidos a protocolos IPv4, incluyendo los que tienen errores 1.3.6.1.2.1.4.3.0" )
            paquetesIPV4 = consultaSNMP( comunidad, ip, '1.3.6.1.2.1.4.3.0' )
            ipInReceives = str(paquetesIPV4) if str(paquetesIPV4).isdigit() else ipInReceives

            #print( "3. Mensajes ICMP echo que ha enviado el agente 1.3.6.1.2.1.5.21.0" )
            echoICMP = paquetesIPV4 = consultaSNMP( comunidad, ip, '1.3.6.1.2.1.6.10.0' )
            icmpOutEchos = str(echoICMP) if str(echoICMP).isdigit() else icmpOutEchos
            
            #print( "4. Segmentos recibidos, incluyendo los que se han recibido con errores 1.3.6.1.2.1.6.10.0" )
            segmentosRecibidos = consultaSNMP( comunidad, ip, '1.3.6.1.2.1.6.10.0')
            tcpInSegs = str(segmentosRecibidos) if str(segmentosRecibidos).isdigit() else tcpInSegs

            #print( "5. Datagramas entregados a usuarios UPD 1.3.6.1.2.1.7.1.0" )
            datagramasUDP = consultaSNMP( comunidad, ip, '1.3.6.1.2.1.7.1.0' )
            udpInDatagrams = str(datagramasUDP) if str(datagramasUDP).isdigit() else udpInDatagrams
        valor = "N:" + ifInUcastPkts + ':' + ipInReceives + ':' + icmpOutEchos + ':' + tcpInSegs + ':' + udpInDatagrams
        rrdtool.update('RRDsAgentes/agente' + idAgente + '.rrd', valor)
        rrdtool.dump('RRDsAgentes/agente' + idAgente + '.rrd','RRDsAgentes/agente' + idAgente + '.xml')
        time.sleep(1)

def crearRRDs( idAgente ):
    print("id" + idAgente)
    ret = rrdtool.create("RRDsAgentes/agente"+ idAgente +".rrd",
	                     "--start",'N',
	                     "--step",'1',
	                     "DS:ifInUcastPkts:COUNTER:600:U:U",
	                     "DS:ipInReceives:COUNTER:600:U:U",
	                     "DS:icmpOutEchos:COUNTER:600:U:U",
	                     "DS:tcpInSegs:COUNTER:600:U:U",
	                     "DS:udpInDatagrams:COUNTER:600:U:U",
	                     "RRA:AVERAGE:0.5:1:700",
	                     "RRA:AVERAGE:0.5:1:700",
	                     "RRA:AVERAGE:0.5:1:700",
	                     "RRA:AVERAGE:0.5:1:700",
	                     "RRA:AVERAGE:0.5:1:700")
    rrdtool.dump( 'RRDsAgentes/agente'+ idAgente +'.rrd', 'RRDsAgentes/agente'+ idAgente +'.xml' )

    if ret:
        print ( rrdtool.error() )

def crearRRDsMonitoreo(idAgente,DS,RRA):
	ret = rrdtool.create("RRDsAgentes/monitoreo"+ idAgente +".rrd",
	                     "--start",'N',
	                     "--step",'3',
                         DS,
                         RRA)
	rrdtool.dump( 'RRDsAgentes/monitoreo'+ idAgente +'.rrd', 'RRDsAgentes/monitoreo'+ idAgente +'.xml' )

	if ret:
	    print ( rrdtool.error() )

def ResumenGeneral():
    #os.system("clear")
    print( "Resumen general de dispositivos" )
    print( "Se estan monitoreando " + str( len( agentes ) ) + " dispositivos.")
    
    archivoAgentes = open( "AgentesRegistrados.txt", "r" )
    for agente in archivoAgentes:
        datosAgente = agente.split(", ")
        estadoDelAgente = str(consultaSNMP(datosAgente[COMUNIDAD],datosAgente[IP],'1.3.6.1.2.1.1.1.0'))
        estado = "DOWN"
        numeroDePuertos = "-"
        consultaSistemaOperativo = str(consultaSNMP(datosAgente[COMUNIDAD], datosAgente[ IP ], '1.3.6.1.2.1.1.1.0'))

        if( estadoDelAgente.split( )[0] != "No"):
            estado = "UP"
            numeroDePuertos = str(consultaSNMP(datosAgente[COMUNIDAD],datosAgente[IP],'1.3.6.1.2.1.2.1.0'))
        print("\n\tAgente : " + datosAgente[IP] + ". Estado: " + estado + ". Numero de puertos: " + numeroDePuertos)

        if( numeroDePuertos.isdigit()):
            print("\t\tEstado de los puertos: ")
            for i  in range(1, int(numeroDePuertos) + 1):                
                estadoPuertoI = str(consultaSNMP(datosAgente[COMUNIDAD],datosAgente[IP],'1.3.6.1.2.1.2.2.1.7.' + str(i)))
                estado = "-"
                if( estadoPuertoI.isdigit()):
                    if( int(estadoPuertoI) == 1):
                        estado = "UP"
                    elif( int(estadoPuertoI) == 2):
                        estado = "DOWN"
                    elif( int(estadoPuertoI) == 3):
                        estado = "TESTING"
                    
                nombrePuertoI = str(consultaSNMP(datosAgente[COMUNIDAD],datosAgente[IP],'1.3.6.1.2.1.2.2.1.2.' + str(i),True))
                if (consultaSistemaOperativo == 'Linux'):
                    nombrePuertoI = nombrePuertoI.split(' = ')[1]
                else:
                    nombrePuertoI = bytes.fromhex( str(nombrePuertoI).split("0x")[1] ).decode('utf-8')
                print("\t\t\t" + str(i) +  " " + estado +" : " + nombrePuertoI)
    archivoAgentes.close()

def AgregarAgente():
    #os.system("clear")
    #Formato del archivo:
    # IP agente | Version SNMP | Comunidad | Puerto
    print( "Ingresa los siguientes datos para agregar un nuevo agente" )    
    ip = input( "Ingresa la direccion IP del agente: " )
    versionSNMP = input( "Ingresa la version SNMP: " )
    comunidad = input( "Ingresa el nombre de la comunidad:: " )
    while( True ):
        puerto = input( "Ingresa el puerto: " )
        if( puerto.isdigit() ):
            break
        else:
            input( "Verifica el puerto. Presiona enter para continuar ... " )

    idAgente = str(int(ultimoID)+1)    
    archivoAgentes = open( "AgentesRegistrados.txt", "a" )
    archivoAgentes.write( ip + ", " + versionSNMP + ", " + comunidad + ", " + puerto + ", " + idAgente + "\n" )
    archivoAgentes.close()
    agentes.append( ip )
    thread_read = threading.Thread(target = MonitorearAgente, args=[ip, comunidad, idAgente])
    thread_read.start()
    return idAgente

def EliminarAgente():    
    #os.system("clear")
    numeroAgenteEliminar = int( ObtenerNumeroAgente( "Selecciona el agente que deseas eliminar" ) )

    if(numeroAgenteEliminar == -1):
        return
    
    agentesAGuardar = []
    archivoAgentes = open ( "AgentesRegistrados.txt", "r" )
    for agenteRegistrado in archivoAgentes:
        if ( (agenteRegistrado.split( ', ' ) )[0] != agentes[numeroAgenteEliminar] ):
            agentesAGuardar.append( agenteRegistrado )
    archivoAgentes.close()

    archivoAgentes = open ( "AgentesRegistrados.txt", "w" )
    archivoAgentes.writelines( agentesAGuardar )
    archivoAgentes.close()
    
    agenteEliminado = agentes[numeroAgenteEliminar]
    agentes.remove( agentes[numeroAgenteEliminar] )
    print( "El agente " + agenteEliminado + " ha sido eliminado" )

def GenerarReporte():
    numeroAgente = ObtenerNumeroAgente( "Selecciona el agente del que deseas obtener el reporte" )
    if( numeroAgente == "-1"):
        return

    while(True):
        tiempoIngresado = input( "Desde hace cuantos minutos deseas obtener el reporte del agente " + agentes[ int(numeroAgente) ] + "? : ")
        if tiempoIngresado.isdigit():
            tiempo_fin = int(tiempoIngresado)
            if(tiempo_fin > 0):
                tiempo_fin *= 60
                break
        input( "Por favor, ingrese una opcion valida. Pulse enter para continuar ... " )
    
    tiempo_actual = int(time.time())
    tiempo_inicio = tiempo_actual - tiempo_fin
    idAgente = ObtenerIdAgente( int(numeroAgente) )
    Graficar(idAgente, tiempo_inicio, "udpInDatagrams", "Cantidad de datagramas", "Datagramas entregados a usuarios UDP", "Datagramas entregados")
    Graficar(idAgente, tiempo_inicio, "ipInReceives", "Cantidad de paquetes", "Paquetes recibidos a protocolos IPv4 con errores", "Paquetes recibidos")
    Graficar(idAgente, tiempo_inicio, "icmpOutEchos", "Cantidad de mensajes", "Mensajes ICMP echo que ha enviado el agente", "Mensajes enviados")
    Graficar(idAgente, tiempo_inicio, "tcpInSegs", "Cantidad de segmentos", "Segmentos recibidos con errores.", "Segmentos recibidos")
    Graficar(idAgente, tiempo_inicio, "ifInUcastPkts", "Cantidad de datagramas", "Datagramas entregados a usuarios UDP", "Datagramas entregados")
    GenerarPDF( idAgente, numeroAgente)

def ObtenerIdAgente( numeroAgente ):
    archivoAgentes = open ( "AgentesRegistrados.txt", "r" )
    for agente in archivoAgentes:
        if( agente.split( ", " )[IP] == agentes[ numeroAgente ] ):
            archivoAgentes.close()
            return agente.split(", ")[ID].split( "\n" )[0]
    archivoAgentes.close()

def ObtenerComunidadAgente( numeroAgente ):
    archivoAgentes = open ( "AgentesRegistrados.txt", "r" )
    for agente in archivoAgentes:
        if( agente.split( ", " )[IP] == agentes[ numeroAgente ] ):
            archivoAgentes.close()
            return agente.split(", ")[COMUNIDAD]
    archivoAgentes.close()

def ObtenerVersionSNMPAgente( numeroAgente ):
    archivoAgentes = open ( "AgentesRegistrados.txt", "r" )
    for agente in archivoAgentes:
        if( agente.split( ", " )[IP] == agentes[ numeroAgente ] ):
            archivoAgentes.close()
            return agente.split(", ")[VERSION_SNMP]
    archivoAgentes.close()

def Graficar(idAgente, tiempo_inicio, dato_a_graficar, label_grafica, titulo_grafica, info_label):
    grafica = rrdtool.graph( "Graficas/" + dato_a_graficar + idAgente + ".png",
                        "--start", str(tiempo_inicio),
                        "--vertical-label=" + label_grafica,
                        "--title=" + titulo_grafica,
                        "DEF:var=RRDsAgentes/agente" + idAgente + ".rrd:" + dato_a_graficar + ":AVERAGE",
                        "AREA:var#0000FF:" + info_label)

def GenerarPDF( idAgente, numAgente):
    numeroAgente = int(numAgente)
    comunidadAgente = ObtenerComunidadAgente(numeroAgente)
    versionSNMPAgente = ObtenerVersionSNMPAgente(numeroAgente)

    nombreArchivo = agentes[ numeroAgente ].replace(".","")
    documento = canvas.Canvas("Reportes/reporteAgente" + nombreArchivo + ".pdf")
    
    encabezado = documento.beginText(40, 800) 

    consultaSistemaOperativo = str(consultaSNMP(comunidadAgente, agentes[ numeroAgente ], '1.3.6.1.2.1.1.1.0'))
    if (consultaSistemaOperativo == 'Linux'):
        sistemaOperativo = "Linux"
    else:
        sistemaOperativo = "Windows"
    encabezado.textLine( "Autor:  Aldo Daniel Mendoza Morales" )
    encabezado.textLine( "Nombre del Sistema Operativo " + sistemaOperativo )
    encabezado.textLine( "Version SNMP: " + versionSNMPAgente )
    
    
    ubicacion = str(consultaSNMP(comunidadAgente, agentes[ numeroAgente ], '1.3.6.1.2.1.1.6.0', True))
    ubicacionGeografica = ubicacion.split("\"")
    if(len(ubicacionGeografica) > 1):
        ubicacion = ubicacion.split("\"")[1]
    else :
        ubicacion = "Sin informacion de ubicacion"
    encabezado.textLine( "Ubicacion geografica: " + ubicacion )

    numeroDePuertos = str(consultaSNMP(comunidadAgente, agentes[ numeroAgente ], '1.3.6.1.2.1.2.1.0'))
    encabezado.textLine( "Numero de puertos: " + numeroDePuertos )

    ultimoInicio = str(consultaSNMP(comunidadAgente, agentes[ numeroAgente ], '1.3.6.1.2.1.1.3.0'))
    if(not ultimoInicio.isdigit()):
        ultimoInicio = "0"
    tiempoInicio = timedelta(seconds = int( int(ultimoInicio)/100 ) )
    encabezado.textLine( "Tiempo de actividad desde el ultimo reinicio: "  + str(tiempoInicio))

    encabezado.textLine( "Comunidad: " + comunidadAgente )

    encabezado.textLine( "IP: " + agentes[ numeroAgente ] )
    documento.drawText( encabezado )
    
    documento.drawImage("SistemasOperativos/logo" + sistemaOperativo + ".png", 400, 720, 100, 100)

    texto = documento.beginText(40, 680)
    texto.textLine( "Grafica 1. Datagramas entregados a usuarios UDP")
    documento.drawText(texto)
    documento.drawImage("Graficas/udpInDatagrams" + idAgente + ".png", 40, 500)

    texto = documento.beginText(40, 480)
    texto.textLine( "")
    texto.textLine( "Grafica 2. Paquetes recibidos a protocolos IPv4, incluyendo los que tienen errores")
    documento.drawText(texto)
    documento.drawImage("Graficas/ipInReceives" + idAgente + ".png", 40, 290)

    texto = documento.beginText(40, 280)
    texto.textLine( "")
    texto.textLine( "Grafica 3. Mensajes ICMP echo que ha enviado el agente")
    documento.drawText(texto)
    documento.drawImage("Graficas/icmpOutEchos" + idAgente + ".png", 40, 90)

    documento.showPage()

    texto = documento.beginText(40, 750)
    texto.textLine( "Grafica 4. Segmentos recibidos, incluyendo los que se han recibido con errores.")
    documento.drawText(texto)
    documento.drawImage("Graficas/tcpInSegs" + idAgente + ".png", 40, 570)

    texto = documento.beginText(40, 550)
    texto.textLine( "Grafica 5. Datagramas entregados a usuarios UDP")
    documento.drawText(texto)
    documento.drawImage("Graficas/ifInUcastPkts" + idAgente + ".png", 40, 370)

    documento.save()

def ObtenerNumeroAgente( mensaje ):
    #os.system( "clear" )
    print( mensaje )

    for i in range( len(agentes) ):
            print(str(i+1) + ". " + agentes[i] )
    print(str( len( agentes )+1 ) + ". Regresar" )

    numeroAgente = input( "Numero del agente: ")

    if( numeroAgente.isdigit() ):
        numeroAgenteSeleccionado = int(numeroAgente) -1

        if( numeroAgenteSeleccionado == len( agentes )):
            return "-1"

        if( 0 <= numeroAgenteSeleccionado < len(agentes) ):
            return str(numeroAgenteSeleccionado)
    
    input( "Por favor, ingrese una opcion valida. Pulse enter para continuar ... " )
    return ObtenerNumeroAgente(mensaje )

def VerificarUmbrales(READY, SET, GO, valor, entidad, grafica):
    global BANDERA_CORREO_READY
    global BANDERA_CORREO_SET
    global BANDERA_CORREO_GO
    try:
        ultimo_valor = float(valor)
    except ValueError:
        ultimo_valor = 0.0
    print(ultimo_valor)
    if( float(READY) <= ultimo_valor < float(SET)):
        print(entidad + " paso el umbral ready")
        if( not BANDERA_CORREO_READY ):
            BANDERA_CORREO_READY = not BANDERA_CORREO_READY
            print("Enviando correo")
            send_alert_attached("Aldo Mendoza (" + entidad + " PASO EL UMBRAL READY)" , grafica)

    elif(float(SET) <= ultimo_valor < float(GO)):
        print(entidad + " paso el umbral set")
        if( not BANDERA_CORREO_SET ):
            BANDERA_CORREO_SET = not BANDERA_CORREO_SET
            print("Enviando correo")
            send_alert_attached("Aldo Mendoza (" + entidad + " PASO EL UMBRAL SET)" , grafica)

    elif(float(GO) <= ultimo_valor):
        print(entidad + " paso el umbral GO")
        if( not BANDERA_CORREO_GO ):
            print("Enviando correo")
            BANDERA_CORREO_GO = not BANDERA_CORREO_GO
            send_alert_attached("Aldo Mendoza (" + entidad + " PASO EL UMBRAL GO)" , grafica)
    else:
        print(entidad + " se encuentra por debajo de los umbrales")

def MonitorearComportamiento(idAgente = -1, comunidad = '', ip = '', OPCION_MENU = False):
    if( idAgente == -1):
        #os.system("clear")
        numeroAgenteMonitorear = int( ObtenerNumeroAgente( "Selecciona el agente que deseas monitorear" ) )

        if(numeroAgenteMonitorear == -1):
            return
        comunidad = ObtenerComunidadAgente(numeroAgenteMonitorear)
        ip = agentes[ numeroAgenteMonitorear ]
        idAgente = ObtenerIdAgente( int(numeroAgenteMonitorear) )
    while(True):
        print("Agente " + ip)
#        CPUs =  consultaSNMPWalk(comunidad, ip, '1.3.6.1.2.1.25.3.3.1.2')
 #       for cpu in CPUs:
#            GraficarUmbrales(idAgente, ip, "CPU"+ cpu, UMBRAL_READY_CPU, UMBRAL_SET_CPU, UMBRAL_GO_CPU, "Carga CPU " + cpu)
        #cpu = "196609"
        #GraficarUmbrales(idAgente, ip, "CPU"+ cpu, UMBRAL_READY_CPU, UMBRAL_SET_CPU, UMBRAL_GO_CPU, "Carga CPU " + cpu)
        GraficarUmbrales(idAgente, ip, "RAM", UMBRAL_READY_RAM, UMBRAL_SET_RAM, UMBRAL_GO_RAM, "Carga RAM ")
        #GraficarUmbrales(idAgente, ip, "Storage", UMBRAL_READY_STORAGE, UMBRAL_SET_STORAGE, UMBRAL_GO_STORAGE, "Almacenamiento ")
        if(not OPCION_MENU):            
            break
        time.sleep(5)

def GraficarUmbrales(idAgente, ip, entidad, UMBRAL_READY, UMBRAL_SET, UMBRAL_GO, labelCarga):
    ultima_lectura = int(rrdtool.last("RRDsAgentes/monitoreo"+ idAgente + ".rrd"))
    tiempo_final = ultima_lectura
    tiempo_inicial = tiempo_final - 120

    nombreGrafica = ip.replace(".","") + entidad
    ret = rrdtool.graphv( "Monitoreo/" + nombreGrafica + ".png",
                    "--start",str(tiempo_inicial),
                    "--vertical-label=Carga del CPU: " + nombreGrafica ,
                    '--lower-limit', '0',
                    '--upper-limit', '100',
                    "DEF:cargaEntidad=RRDsAgentes/monitoreo" + idAgente + ".rrd:" + entidad +":AVERAGE",
                    "CDEF:carga=cargaEntidad,"+ UMBRAL_READY +",LT,cargaEntidad,0,IF",
                    "CDEF:umbralReady=cargaEntidad,"+ UMBRAL_READY +",GT,cargaEntidad,0,IF",
                    "CDEF:umbralSet=cargaEntidad,"+ UMBRAL_SET +",GT,cargaEntidad,0,IF",
                    "CDEF:umbralGo=cargaEntidad,"+ UMBRAL_GO +",GT,cargaEntidad,0,IF",
                    "VDEF:cargaMAX=cargaEntidad,MAXIMUM",
                    "VDEF:cargaMIN=cargaEntidad,MINIMUM",
                    "VDEF:cargaLAST=cargaEntidad,LAST",
                    "AREA:carga#988D8D:" + labelCarga + " menor que " + UMBRAL_READY,
                    "AREA:umbralReady#50DA23:" + labelCarga + " mayor que " + UMBRAL_READY,
                    "AREA:umbralSet#FF8B00:" + labelCarga + " mayor que " + UMBRAL_SET,
                    "AREA:umbralGo#FF0000:" + labelCarga + " que " + UMBRAL_GO,
                    "HRULE:" + UMBRAL_READY + "#50DA23:Umbral ready 1 - " + UMBRAL_READY +"%",
                    "HRULE:" + UMBRAL_SET + "#FF8B00:Umbral set " + UMBRAL_SET +" - " + UMBRAL_GO +"%",
                    "HRULE:" + UMBRAL_GO + "#FF0000:Umbral go " + UMBRAL_GO +" - 100%",
                    "PRINT:cargaLAST:%6.2lf %S",
                    "GPRINT:cargaMAX:%6.2lf %SMAX",
                    "GPRINT:cargaMIN:%6.2lf %SMIN",
                    "GPRINT:cargaLAST:%6.2lf %SLAST")
    VerificarUmbrales(UMBRAL_READY, UMBRAL_SET, UMBRAL_GO, ret['print[0]'], entidad, nombreGrafica)

def ModificarUmbrales():
    while(True):
        #os.system( "clear" )
        print( "Selecciona el umbral que quieres modificar" )
        print( "1. CPUs" )
        print( "2. RAM" )
        print( "3. Almacenamiento" )
        opcion = input( "Ingresa una opcion: " )

        if( opcion == "4"):
            return

        if( opcion.isdigit() ):
            umbral = int( opcion )
            if( 0 < umbral < 4):
                umbralModificar = ''
                if( umbral == 1): 
                    global UMBRAL_READY_CPU, UMBRAL_SET_CPU, UMBRAL_GO_CPU
                    umbralModificar = "CPUs"
                    print(UMBRAL_READY_CPU + " " + UMBRAL_SET_CPU + " " + UMBRAL_GO_CPU)
                elif( umbral == 2): 
                    umbralModificar = "RAM"
                    global UMBRAL_READY_RAM, UMBRAL_SET_RAM, UMBRAL_GO_RAM
                    print(UMBRAL_READY_RAM + " " + UMBRAL_SET_RAM + " " + UMBRAL_GO_RAM)
                else:
                    umbralModificar = "almacenamiento"
                    global UMBRAL_READY_STORAGE, UMBRAL_SET_STORAGE, UMBRAL_GO_STORAGE
                    print(UMBRAL_READY_STORAGE + " " + " " + UMBRAL_SET_STORAGE + " " + UMBRAL_GO_STORAGE)
                while(True):
                    nuevosUmbrales = input( "Ingresa los nuevos umbrales para " + umbralModificar +"  de la siguiente manera: UMBRAL_READY UMBRAL_SET UMBRAL_GO: " )
                    umbrales = nuevosUmbrales.split(" ")
                    if( len(umbrales) == 3):
                        if( umbral == 1): 
                            UMBRAL_READY_CPU = umbrales[0]
                            UMBRAL_SET_CPU = umbrales[1]
                            UMBRAL_GO_CPU = umbrales[2]
                        elif( umbral == 2): 
                            UMBRAL_READY_RAM = umbrales[0]
                            UMBRAL_SET_RAM = umbrales[1]
                            UMBRAL_GO_RAM = umbrales[2]
                        else:
                            UMBRAL_READY_STORAGE = umbrales[0]
                            UMBRAL_SET_STORAGE = umbrales[1]
                            UMBRAL_GO_STORAGE = umbrales[2]
                        break
                    input("Verifique los umbrales. Pulse enter para continuar ... ")
                break
            input("Verifique el umbral seleccionado. Pulse enter para continuar ... ")            

def AdministrarConfiguracion():
    #while(True):
    os.system( "clear" )
    HOST = input( "Ingresa la direccion de la interface a la que te deseas conectar: " )
    usuario = input( "Ingresa el usuario: " )
    password = input( "Ingresa el password: " )
        
    while(True):
        os.system( "clear" )
        print("1. Ver archivo de configuracion")
        print("2. Modificar archivo de configuracion")
        print("3. Salir")
        opcion = input( "Ingresa una opcion: " )

        if(opcion == "1"):
            print( ObtenerArchivoConfiguracion(HOST, usuario, password) )
            input( "Pulsa enter para continuar")
        elif( opcion == "2"):            
            archivoConfiguracion = ObtenerArchivoConfiguracion(HOST, usuario, password)
            interfaces = ObtenerNumeroInterfaces(archivoConfiguracion)
            
            while(True):
                os.system( "clear" )
                print("Modificar archivo de configuracion")
                print("1. Modificar nombre de Host")
                print("2. Modificar interface ethX")
                print("3. Actualizar cambios")
                print("4. Generar reporte")
                print("5. Regresar")
                opcion = input( "Ingresa una opcion: " )

                if( opcion == "1"):
                    nombreHost = input("Ingresa el nuevo nombre del HOST: ")
                    ModificarArchivoConfiguracion(HOST, usuario, password, nombreHost,'', '', '', '')
                elif( opcion == "2" ):
                    numeroInterface = input("Ingresa el numero de la interface: ")
                    ipInterface = input("Ingresa la ip: ")
                    mascara = input("Ingresa la mascara (En formato /XX): ")
                    shutdown = input("Deseas establecer shutdown? y/n: ")
                    ModificarArchivoConfiguracion(HOST, usuario, password,'',int(numeroInterface), ipInterface, mascara, shutdown == "y" )
                elif( opcion == "3" ):
                    print("Actualizando datos en router " + HOST + " ...")
                    ActualizarArchivoConfiguracion(HOST, usuario, password)
                    print("Datos actualizados")
                elif( opcion == "4" ):
                    GenerarReporteInterface(HOST)
                elif( opcion == "5" ):
                    break
                else: 
                    print( "Por favor, ingrese una opcion valida" )
        elif( opcion =="3" ):
            break
        else: 
            print( "Por favor, ingrese una opcion valida" )

def GenerarReporteInterface(HOST):
    nombreArchivo = "startup-config" + HOST.replace(".","")
    documento = canvas.Canvas("I" + nombreArchivo + ".pdf")
    
    encabezado = documento.beginText(40, 800) 

    encabezado.textLine( "Autor:  Aldo Daniel Mendoza Morales" )
    encabezado.textLine( " " )
    encabezado.textLine( " " )
    encabezado.textLine( " " )
    encabezado.textLine( "Host: " + HOST )
    documento.drawText( encabezado )
    
    documento.drawImage("router.png", 400, 720, 100, 100)    

    maximo = 680
    texto = documento.beginText(40, maximo+10)
    texto.textLine( "Resumen del dispositivo ")
    documento.drawText(texto)

    archivoConfiguracion = open ( "startup-config" + HOST.replace(".",""), "r" )    
    archivo = archivoConfiguracion.read().split('!')        
    archivoConfiguracion.close()
    
    archivoConfiguracion = open ( "startup-config" + HOST.replace(".",""), "r" )    
    nombreHost = archivoConfiguracion.readline().split("\n")
    archivoConfiguracion.close()

    maximo = maximo - 10
    texto = documento.beginText(40, maximo)
    texto.textLine( "hostname " + nombreHost[0])
    documento.drawText(texto)

    i = 0
    for posicion in archivo:
        if(len(posicion.split('loopback')) > 1):
            break
        i += 1

    
    for l in range(i+1, len(archivo)-1):        
        for t in archivo[l].split('\n'):
            maximo = maximo - 15
            texto = documento.beginText(40, maximo)
            texto.textLine(t)
            documento.drawText(texto)
            if( maximo <= 90):
                maximo = 680
                documento.showPage()
    documento.save()
    input("Reporte generado ...")

def ObtenerArchivoConfiguracion(HOST, usuario, password):
    AccionesTelnet(HOST, usuario, password, "copy running-config startup-config")
    AccionesFTP(HOST, usuario, password, True)
    archivoConfiguracion = open ( "startup-config" + HOST.replace(".",""), "r" )    
    return archivoConfiguracion.read()

def ModificarArchivoConfiguracion(HOST, usuario, password, hostname ,numeroInterface, ipInterface, mascara,YNShutdown):
    archivoConfiguracion = open ( "startup-config" + HOST.replace(".",""), "r" )
    
    if(hostname != ""):
        print("Modificando host ... ")
        nombreHost = "hostname " + hostname +"\n"
    else:
        nombreHost = archivoConfiguracion.readline()
    archivo = archivoConfiguracion.read().split('!')    
    archivoConfiguracion.close()

    archivo[0] = nombreHost

    if(ipInterface != ""):
        print("Modificando la interface " + str(numeroInterface) +" ... ")
        i = 0
        for posicion in archivo:
            if(len(posicion.split('loopback')) > 1):
                break
            i += 1
    
        for l in range(i+1, len(archivo)):            
            if(YNShutdown):
                shutdown = "no shutdown"
            else:
                shutdown = "shutdown"
            if( l - i - 1 == numeroInterface):
                interfaz = "\ninterface ethernet eth" + str(numeroInterface) + "\n"+ "  " + "ip address " + ipInterface + mascara +"\n"+ "  " + "ip mtu 1500\n"+ "  " + shutdown + "\n"
                archivo[l] = interfaz
    

    localfile = open("startup-config" + HOST.replace(".",""), 'w')
    i = 0
    for linea in archivo:
        i+=1
        localfile.write(linea)
        if(i < len(archivo)):
            localfile.write("!")
    localfile.close()

    AccionesFTP(HOST, usuario, password, False)
    print("Los cambios se han realizado y enviado con exito")
    input("Pusla enter para continuar ...")

def ActualizarArchivoConfiguracion(HOST, usuario, password):
    archivoConfiguracion = open ( "startup-config" + HOST.replace(".",""), "r" )    
    archivo = archivoConfiguracion.read().split('!')        
    archivoConfiguracion.close()
    
    archivoConfiguracion = open ( "startup-config" + HOST.replace(".",""), "r" )    
    nombreHost = archivoConfiguracion.readline()
    print(nombreHost)
    archivoConfiguracion.close()
    
    print("Actualizando hostname ...")
    AccionesTelnet(HOST, usuario, password, nombreHost)
    i = 0
    for posicion in archivo:
        if(len(posicion.split('loopback')) > 1):
            break
        i += 1

    print("Actualizando interfaces ... ")
    for l in range(i+1, len(archivo)-1):
        AccionesTelnet(HOST, usuario, password, '', archivo[l].split('\n'))
    
    
    print("Los cambios se han realizado")
    input("Pulse enter para continuar ... ")    

def AccionesFTP(HOST, usuario, password, descarga):
    try:
        tn = telnetlib.Telnet(HOST,23,5)
        tn.read_until(b"login: ",5)
        tn.write(usuario.encode('ascii') + b"\n")
        if password:
            tn.read_until(b"Password: ",5)
            tn.write(password.encode('ascii') + b"\n")
        tn.write(b"enable\n")
        tn.write(b"config\n")
        print("habilitando FTP")
        tn.write(b"service ftp\n")
        print("Servidor ftp habilitado")

        ftp = ftplib.FTP( HOST )        
        ftp.login(usuario, password)
        filename = "startup-config" + HOST.replace(".","")
        if( descarga ):
            localfile = open(filename, 'wb')
            ftp.retrbinary('RETR startup-config', localfile.write, 1024)
        else:
            ftp.storbinary('STOR startup-config', open(filename, 'rb'))
        ftp.quit()
        
        tn.write(b"exit\n")
        tn.write(b"exit\n")
        print(tn.read_all().decode('ascii'))    
    except:    
        print("Error en FTP")
        time.sleep(5)

def AccionesTelnet(HOST, usuario, password, acciones, varias = ''):
    conectado = False
    try:
        tn = telnetlib.Telnet(HOST,23,5)
        tn.read_until(b"login: ",5)
        tn.write(usuario.encode('ascii') + b"\n")
        if password:
            tn.read_until(b"Password: ",5)
            tn.write(password.encode('ascii') + b"\n")
            conectado = True
        tn.write(b"enable\n")
        tn.write(b"config\n")
        print(acciones)
        if(acciones != ''):
            tn.write(acciones.encode('ascii') + b"\n")
        if(varias != ''):
            for v in varias:
                if(v != ''):
                    print(v)
                    tn.write(v.encode('ascii') + b"\n")
            tn.write(b"exit\n")
        tn.write(b"exit\n")
        tn.write(b"exit\n")
        print(tn.read_all().decode('ascii'))
    except:    
        print("Error Telnet")
    if( acciones == ""):
        return conectado

def ObtenerNumeroInterfaces(contenidoArchivo):
    return 8

agentes = []
ultimoID = InicializarVariables()

while(True):
    #os.system( "clear" )
    print( "1. Resumen general" )
    print( "2. Agregar agente" )
    print( "3. Eliminar agente" )
    print( "4. Generar reporte" )
    print( "5. Monitorear agente" )
    print( "6. Modificar umbrales" )
    print( "7. Administrador de configuracion" )
    print( "8. Salir" )
    opcion = input( "Ingresa una opcion: " )

    if   (opcion == "1"):
        ResumenGeneral()
    elif (opcion == "2"):
        ultimoID = AgregarAgente()
    elif (opcion == "3"):
        EliminarAgente()
    elif (opcion == "4"):
        GenerarReporte()
    elif (opcion == "5"):
        MonitorearComportamiento(OPCION_MENU = True)
    elif (opcion == "6"):
        ModificarUmbrales()        
    elif (opcion == "7"):
        AdministrarConfiguracion()
    elif (opcion == "8"):
        print( "Salir" )
        agentes.clear()
        break
    else: 
        print( "Por favor, ingrese una opcion valida" )
    input( "Pulse enter para continuar ... ")
