import rrdtool
import time
import threading
from getSNMP import consultaSNMP

def crearRRDs():
    ret = rrdtool.create("rrdsRPN.rrd",
	                     "--start",'N',
	                     "--step",'2',
	                     "DS:cpu:GAUGE:600:U:U",
	                     "DS:cpu2:GAUGE:600:U:U",
	                     "RRA:AVERAGE:0.5:1:700",
	                     "RRA:AVERAGE:0.5:1:700",)
    rrdtool.dump( 'rrdsRPN.rrd', 'rrdsRPN.xml' )

    if ret:
        print ( rrdtool.error() )

def MonitorearAgente():
    while(True):
        cpu1 = cpu2 = "0"
        estadoDelAgente = str(consultaSNMP( comunidad, ip, '1.3.6.1.2.1.1.1.0'))
        if( estadoDelAgente.split( )[0] != "No" ):
            cpu = consultaSNMP( comunidad, ip, '1.3.6.1.2.1.25.3.3.1.2.196609' )
            cpu1 = str(cpu) if str(cpu).isdigit() else cpu1

            cpu = consultaSNMP( comunidad, ip, '1.3.6.1.2.1.25.3.3.1.2.196610' )
            cpu2 = str(cpu) if str(cpu).isdigit() else cpu2

            print( cpu1 + " -- " + cpu2)
            valor = "N:" + cpu1 + ':' + cpu2
            rrdtool.update('rrdsRPN.rrd', valor)
            rrdtool.dump('rrdsRPN.rrd','rrdsRPN.xml')
            time.sleep(2)


def Graficar():
    ultima_lectura = int(rrdtool.last("rrdsRPN.rrd"))
    tiempo_final = ultima_lectura
    tiempo_inicial = tiempo_final - 120
    ret = rrdtool.graphv( "OperadorBooleano.png",
                     "--start",str(tiempo_inicial),
                     "--end",str(tiempo_final),
                     "--vertical-label=Cpu load",
                    '--lower-limit', '0',
                    '--upper-limit', '100',
                     "DEF:cargaCPU=rrdsRPN.rrd:cpu:AVERAGE",
                     "CDEF:umbral5=cargaCPU,25,LT,0,cargaCPU,IF",
                     "VDEF:cargaMAX=cargaCPU,MAXIMUM",
                     "AREA:cargaCPU#00FF00:Carga del CPU",
                     "AREA:umbral5#FF9F00:Carga CPU mayor que 25",
                     "HRULE:25#FF0000:Umbral 1 - 25%")
    
    ret = rrdtool.graphv( "OperadorAritmetico.png",
                     "--start",str(tiempo_inicial),
                     "--end",str(tiempo_final),
                     "--vertical-label=Cpu load",
                    '--lower-limit', '0',
                    '--upper-limit', '100',
                     "DEF:cargaCPU=rrdsRPN.rrd:cpu:AVERAGE",
                     "CDEF:umbral5=cargaCPU,2,*,45,GT,cargaCPU,2,*,0,IF",
                     "CDEF:umbral51=cargaCPU,2,*,45,GT,0,cargaCPU,2,*,IF",
                     "AREA:umbral5#FF9F00:Carga CPU * 2 mayor que 45",
                     "AREA:umbral51#00FF00:Carga CPU * 2 menor que 45",
                     "HRULE:45#FF0000:Umbral 1 - 45%")

    ret = rrdtool.graphv( "OperadorComparacion.png",
                     "--start",str(tiempo_inicial),
                     "--end",str(tiempo_final),
                     "--vertical-label=Cpu load",
                    '--lower-limit', '0',
                    '--upper-limit', '100',
                     "DEF:cargaCPU1=rrdsRPN.rrd:cpu:AVERAGE",
                     "DEF:cargaCPU2=rrdsRPN.rrd:cpu2:AVERAGE",
                     "CDEF:umbral5=cargaCPU2,cargaCPU1,EQ,100,0,IF",
                     "AREA:umbral5#FF9F00:Carga CPU 1 = Carga CPU 2",
                     "HRULE:45#FF0000:Umbral 1 - 100%")

crearRRDs()

comunidad = "comunidadSNMP"
ip = "127.0.0.1"

thread_read = threading.Thread(target = MonitorearAgente, args=[])
thread_read.start()

while(True):
    input("Pulsa enter para graficar")
    Graficar()