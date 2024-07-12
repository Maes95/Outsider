# Outsider: Un juego online en tiempo real

### Trabajo Fin de Grado - Ingeniería de Computadores

<br>

## Introducción

En este repositorio se almacena en su totalidad el trabajo de fin de grado de Ingeniería de Computadores (URJC)
del alumno Javier Raúl Alonso Tejera. A continuación
se muestran las instrucciones para poder desplegar la aplicación
en la nube y un tutorial para ejecutar los tests automáticos implementados.

<br>

## Instrucciones de despliegue

En este apartado se indican las instrucciones a la hora de realizar un despliegue de la aplicación a través de AWS. A continuación se indican todos los mandatos que se deben ejecutar y referenciar en las instrucciones.

    sudo ssh -i "privatekeys.pem" ubuntu@machineDir...

    git clone https://github.com/Javiex7/Outsider.git

    cd Outsider/OutsiderProject
    sudo docker compose -f docker-compose.yaml up --build
<br>
<ol>
<li>
En primer lugar, es necesario tener una máquina EC2 preparada para poder conectarse a ella. Desde el panel de control de EC2 se pueden lanzar nuevas instancias y gestionar las que ya han sido configuradas y lanzadas anteriormente. Para este proyecto se está haciendo uso de la máquina nombrada como "outsider-machine"
</li> <br>

<li>
Con la máquina lista, es necesario conectarse a ella mediante el uso del mandato ssh y las claves privadas generadas
a la hora de crear la instancia de la máquina.
Se destaca que se debe sustituir "machineDir" por la dirección DNS de la máquina en cuestión. Esta dirección y demás información
relacionada con la conexión a una máquina EC2 se puede encontrar en la sección de "Conectarse a una instancia" dentro de la página de 
gestión de EC2.
</li> <br>

<li>
Ya en el directorio principal, se puede crear una carpeta adicional o descargar el repositorio del código directamente. 
Este repositorio debería ser accesible para cualquier usuario y para descargarlo desde 
la terminal simplemente es necesario hacer uso del mandato `git clone''.
</li> <br>

<li>
Ahora solo quedaría acceder al directorio principal y ejecutar el mandato de Docker para ejecutar los contenedores
descritos en el fichero "docker-compose.yaml".
</li> <br>

<li>
Después del tiempo de descarga e instalación necesario, la aplicación estará lista para su uso mientras se mantenga activa la
máquina EC2.
</li> <br>
</ol>

<br>

## Tutorial de testing

En este apartado se indican los pasos a seguir para poder ejecutar los tests de la aplicación sin complicaciones. Se recomienda hacer
la configuración necesaria en un sistema Unix ya que es donde se ha trabajado la aplicación y, más adelante, se indicará hacer uso de mandatos
específicos de Unix.

<ol>
<li>
Lo primero es tener el proyecto actualizado. Este repositorio debería ser accesible para cualquier usuario.
</li> <br>

<li>
Para la ejecución de los tests en indispensable la instalación tanto de Python como de Docker.
Con estos programas instalados en el sistema, es necesario acceder al repositorio para la configuración básica.
</li> <br>

<li>

Dentro del proyecto, son necesarios la instalación de varios elementos en el dispositivo, específicamente Django y los paquetes
pertinentes. Para evitar problemas, se recomienda descargar los elementos listados en el "requirements.txt" dentro de la carpeta principal "OutsiderProject". Esta instalación se puede realizar fácilmente mediante el mandato:<br><br>

    pip install -r requirements.txt
<br>
</li> <br>

<li>
A continuación, se requiere ejecutar un contenedor en Docker encargado de gestionar el servidor Redis para
que se haga uso en los tests. Mediante el siguiente mandato se puede poner en ejecución el servicio:<br><br>

    docker run --rm -p 6379:6379 redis:7
<br>
<li>
Antes de poder ejecutar los tests, se debe configurar un variable de entorno para indicar el uso de
este servidor Redis. Para ello habría que acceder a `OutsiderProject/outsider/settings.py'' y modificar
el flag booleano denominado `TEST'' y asegurarse que su valor sea True (línea 92).
</li> <br>

<li>
Finalmente, el sistema puede ejecutar los tests. Para ello solo habría que ejecutar el mandato pytest desde el directorio padre "OutsiderProject":<br><br>

    pytest
<br>
</li> <br>

</ol>


az group create --name outsider-group --location "South Central US"