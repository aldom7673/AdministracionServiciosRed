from pysnmp.hlapi import *
from getSNMP import consultaSNMP
from getSNMP import consultaSNMPWalk

host = "10.100.79.110"
version = "1"
comunidad = "AldoMendoza4cv5"
puerto = 161

# hrProcessorLoad	 = "1.3.6.1.2.1.25.3.3.1.2"
# Ejecutar res = consultaSNMPWalk() y ejecutar hrProcessorLoad + res[i] 
# para obtener la carga de cada procesador

# hrStorageTable = "1.3.6.1.2.1.25.2.3.1"
# entidad = "Physical Memory"
# Ejecutar res = consultaSNMPWalk(hrStorageTable + ".3"), entidad) para obtener el numero de la entidad 
# especificada y ejecutar hrStorageTable + ".4" + res para obtener el uso de la RAM

# hrStorageTable = "1.3.6.1.2.1.25.2.3.1"
entidad = "C:" # "/" 
# Ejecutar res = consultaSNMPWalk(..., entidad) para obtener el numero la entidad especificada,
# (si es un disco en Windows, especificarlo enviando al final una bandera en True) y ejecutar
# hrStorageTable + ".5" + res para obtener el uso de disco 

print( consultaSNMPWalk(comunidad,host,'1.3.6.1.2.1.25.2.3.1.3', entidad, True) )
