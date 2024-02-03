<template>
  <div v-if="user.state == 'PLAYER_TURN'">
    <v-chip variant="flat" size="x-large">
      <v-icon start color="#9cb443" icon="mdi mdi-circle" />
      <h2>Es tu turno!</h2>
    </v-chip>
    <h3 class="mx-auto" style="margin-top: 1rem; max-width: 20rem">
      Escribe una palabra semejante a la
      <u v-if="user.outsider" style="color: #ffac2b"> contraseña</u>
      <u v-else style="color: #47ffda"> contraseña</u>
      fijándote en las palabras escritas por los otros jugadores
      <p v-if="user.outsider" style="margin-top: 0.5rem;">
        Recuerda que los inocentes usan otra contraseña diferente, ten cuidado
      </p>
    </h3>
  </div>

  <div v-else-if="user.state == 'OUT'">
    <v-chip variant="flat" size="x-large">
      <v-icon start color="white" icon="mdi mdi-circle" />
      <h2>Estás eliminado...</h2>
    </v-chip>
    <h3 class="mx-auto" style="margin-top: 1rem; max-width: 20rem">
      Puedes salir de la partida u observar como continuan los otros jugadores
    </h3>
  </div>

  <div v-else>
    <v-chip variant="flat" size="x-large">
      <v-icon start color="#ffac2b" icon="mdi mdi-circle" />
      <h2>Espera a tu turno...</h2>
    </v-chip>
  </div>
</template>

<script setup>
var user = defineModel("user");
</script>

<script></script>
