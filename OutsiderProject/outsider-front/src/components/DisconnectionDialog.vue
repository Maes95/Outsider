<template>
  <v-dialog persistent v-model="disconnection" max-width="650" width="auto">
    <v-card color="#323232" title="Ups...">
      <v-card-text> {{ text }}</v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>

        <v-btn
          style="margin: 0.5rem"
          variant="tonal"
          text="Okay..."
          rounded
          class="text-none"
          @click="returnToHome()"
        ></v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
var disconnection = defineModel("disconnection");
</script>

<script>
export default {
  data: () => ({
    text: "Uno o más jugadores han abandonado la sesión actual y faltan jugadores para continuar la partida. Puedes volver al menú e intentar jugar nuevamente",
  }),

  methods: {
    returnToHome() {
      this.$router.push("/");
    },
  },
};
</script>
