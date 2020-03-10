import os
import threading
import time
import rrdtool
import datetime
from datetime import timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from getSNMP import consultaSNMP
from reportlab.lib.utils import ImageReader

IP = 0
VERSION_SNMP = 1
COMUNIDAD = 2
PUERTO = 3
ID = 4

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

def MonitorearAgente(ip, comunidad, idAgente):
    crearRRDs(idAgente)
    #print("Monitoreando agente ", ip)
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

def ResumenGeneral():
    os.system("clear")
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
    os.system("clear")
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
    os.system("clear")
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
    os.system( "clear" )
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

def DeteccionDeComportamientos():
    print( "" )
agentes = []
ultimoID = InicializarVariables()

while(True):
    os.system( "clear" )
    print( "1. Resumen general" )
    print( "2. Agregar agente" )
    print( "3. Eliminar agente" )
    print( "4. Generar reporte" )
    print( "5. Salir" )
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
        DeteccionDeComportamientos()
    elif (opcion == "6"):
        print( "Salir" )
        agentes.clear()
        break
    else: 
        print( "Por favor, ingrese una opcion valida" )
    input( "Pulse enter para continuar ... ")