<template>
  <v-col cols="auto">
    <v-dialog width="auto">
      <template v-slot:activator="{ props }">
        <v-btn
          v-bind="props"
          class="text-none"
          rounded
          variant="text"
          prepend-icon="mdi-information-outline"
        >
          Cómo jugar
        </v-btn>
      </template>

      <template v-slot:default="{ isActive }">
        <v-card color="#323232" title="Cómo jugar">
          <v-card-text>
            <p style="margin-bottom: 1rem">
              En este juego, todos los jugadores juegan como
              <span style="color: #9cb443"> Inocentes</span>, a excepción de uno
              conocido como el <span style="color: #ffac2b"> Outsider</span>.
            </p>

            <p style="margin-bottom: 1rem">
              Al empezar la partida, los jugadores
              <span style="color: #9cb443"> Inocentes</span> reciben una
              <span style="color: #47ffda"> palabra secreta o contraseña</span>,
              como por ejemplo <span style="color: #47ffda"> "Hoja"</span>.
              <u> Siguiendo un orden</u>
              predeterminado (con el primer jugador elegido al azar), cada
              participante debe escribir una palabra relacionada con su palabra
              secreta para indicar a los demás que conocen la palabra asignada.
            </p>

            <p style="margin-bottom: 1rem">
              Por ejemplo si la contraseña es la palabra
              <span style="color: #47ffda"> "Hoja"</span> unas palabras que
              alienten a esta contraseña podrían ser
              <span style="color: #47ffda"> "Árbol"</span>,
              <span style="color: #47ffda"> "Libro"</span> o ,
              <span style="color: #47ffda"> "Afeitado"</span>.
            </p>

            <v-chip style="margin-bottom: 1rem">
              No está permitido repetir palabras
            </v-chip>

            <p style="margin-bottom: 1rem">
              El jugador designado como
              <span style="color: #ffac2b"> Outsider</span>, quien no tiene
              conocimiento de la palabra secreta, debe tratar de deducirla a
              partir de las palabras previamente mencionadas y decir una palabra
              que no levante sospechas. El
              <span style="color: #ffac2b"> Outsider</span> también posee su
              propia "contraseña" diferente a la contraseña original que le
              puede servir de ayuda o llevarle a más confusión.
            </p>

            <p style="margin-bottom: 1rem">
              Después de que todos los jugadores hayan compartido una palabra,
              se lleva a cabo una <u>votación simultánea</u>, donde cada jugador
              vota por la persona que creen que es el
              <span style="color: #ffac2b"> Outsider</span>. En el caso de que
              el <span style="color: #ffac2b"> Outsider</span> reciba la mayoría
              de los votos, se le otorgará una <u>última oportunidad</u> para
              ganar adivinando la
              <span style="color: #47ffda"> contraseña</span>.
            </p>

            <p style="margin-bottom: 1rem">
              Si el <span style="color: #ffac2b"> Outsider</span> no es el
              jugador más votado, en lugar de ganar, el jugador
              <span style="color: #9cb443"> Inocente </span> más votado saldrá
              de la partida y se realizará otra ronda, dónde cada jugador
              volverá a decir una palabra y se producirá otra votación. El
              <span style="color: #ffac2b"> Outsider</span> ganará si solo
              quedan dos personas en la partida (y él es una de ellas). El resto
              de los<span style="color: #9cb443"> Inocentes </span> ganarán si
              logran descubrirlo/votarlo y este no adivina la palabra secreta
            </p>

            <p>
              Si el número de jugadores es grande puede haber
              <span style="color: #ffac2b"> Outsiders </span> adicionales...
            </p>
          </v-card-text>

          <v-card-actions>
            <v-spacer></v-spacer>

            <v-btn
              style="margin: 0.5rem"
              variant="tonal"
              text="Okay"
              rounded
              class="text-none"
              @click="isActive.value = false"
            ></v-btn>
          </v-card-actions>
        </v-card>
      </template>
    </v-dialog>
  </v-col>
</template>

<script></script>
