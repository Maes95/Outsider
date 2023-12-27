<template>
  <v-col cols="auto">
    <v-dialog max-width="650" width="auto">
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
          <v-card-text> {{ gameRules }}</v-card-text>

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

<script>
export default {
  data: () => ({
    gameRules:
      "Todos los jugadores, salvo 1 (el outsider), reciben una palabra secreta (p.e. Hoja).  Todos los jugadores, en orden (siendo el primero aleatorio) y uno tras otro, tienen que ir diciendo cada uno una palabra que indique a los demás que sabe la palabra secreta (p.e. Espada, Libro, Afeitado ...). No se pueden repetir palabras. El jugador que no ha recibido la palabra secreta (el outsider) deberá intentar deducir a partir de las palabras previas cuál es la palabra secreta y decir una palabra para pasar desapercibido.  Cuando todos los jugadores hayan dicho una palabra, se produce una votación simultánea dónde todos los jugadores votan quién creen que es el outsider.  Si el outsider es el más votado, tiene una última oportunidad de ganar, que será adivinar la palabra secreta.  Si el outsider no es el más votado, el outsider gana la partida.",
  }),
};
</script>
