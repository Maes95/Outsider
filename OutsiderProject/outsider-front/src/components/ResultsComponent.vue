<template>
  <v-card color="#323232">
    <v-card-text>
      <h3 v-if="playerOut">
        <h1 style="margin-bottom: 1rem; font-size: x-large">
          <!-- Last chance -->
          <span v-if="playerOut.outsider && !lastChanceEnd">
            ¿Victoria de los
            <span style="color: #9cb443"> Jugadores Inocentes</span>?
          </span>

          <!-- Last chance ended -->
          <span v-else-if="playerOut.outsider && lastChanceEnd">
            <!-- Ousider win -->
            <div v-if="result">
              Victoria del
              <span style="color: #ffac2b">
                Jugador Outsider
                <v-icon icon="mdi-emoticon-devil-outline" />
              </span>
            </div>
            <!-- Players win -->
            <div v-else>
              Victoria de los
              <span style="color: #9cb443">
                Jugadores Inocentes <v-icon icon="mdi-emoticon-happy-outline" />
              </span>
            </div>
          </span>

          <!-- Ousider win -->
          <span v-else>
            Victoria del
            <span style="color: #ffac2b">
              Jugador Outsider
              <v-icon icon="mdi-emoticon-devil-outline" />
            </span>
          </span>
        </h1>

        <p>
          <span style="color: #47ffda">{{ playerOut.username }} </span>

          <!-- Last chance -->
          <span v-if="playerOut.outsider && !lastChanceEnd">
            tendría que ser eliminado ya que es el
            <span style="color: #ffac2b"> Outsider</span>, pero tendrá una
            oportunidad adicional para ganar adivinando la
            <span style="color: #47ffda">contraseña</span>.

            <p v-if="playerOut.id == user.id" style="margin-top: 1rem">
              <v-divider
                style="margin-top: 2rem; margin-bottom: 2rem"
                :thickness="3"
              />

              ¡Adelante
              <span style="color: #47ffda"> {{ user.username }} </span>!

              <v-form @submit.prevent ref="lastChanceVote">
                <v-text-field
                  class="mx-auto"
                  style="margin-top: 1rem; margin-bottom: 1rem"
                  v-model="lastChanceGuess"
                  label="Última oportunidad..."
                  clearable
                  @keydown.space.prevent
                  :rules="lastChanceRules"
                />

                <v-btn
                  class="text-none"
                  style="margin-bottom: 1rem"
                  @click="lastChanceVote()"
                  :rounded="true"
                  :disabled="!lastChance"
                  lastChanceVote
                >
                  Enviar
                </v-btn>
              </v-form>
            </p>
          </span>

          <!-- Last chance ended -->
          <span v-else-if="playerOut.outsider && lastChanceEnd">
            <!-- Ousider win -->
            <span v-if="result">
              ha deducido la contraseña de <u>forma correcta</u> y aunque se
              haya descubierto su rol como
              <span style="color: #ffac2b"> Outsider</span>, ha ganado esta
              partida.
            </span>
            <!-- Players win -->
            <span v-else>
              ha intentado adivinar la contraseña
              <u> de forma errónea</u> además de haber sido descubierto como
              <span style="color: #ffac2b"> Outsider</span>, por ello, han
              ganado de forma aplastante los
              <span style="color: #9cb443"> Jugadores Inocentes</span>.
            </span>
          </span>

          <!-- Ousider win -->
          <span v-else>
            ha sido el jugador más votado! Pero era
            <span style="color: #9cb443"> Inocente</span>... Por ello ha ganado
            el jugador <span style="color: #ffac2b"> Outsider</span>.
          </span>
        </p>
      </h3>

      <h3 v-else>
        <h1 style="margin-bottom: 1rem; font-size: x-large">Empate...</h1>
        <p>Empate en las votaciones. Nadie gana U.u</p>
      </h3>
    </v-card-text>

    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn
        style="margin: 0.5rem"
        variant="tonal"
        text="Terminar partida"
        rounded
        class="text-none"
        :disabled="lastChance && !lastChanceEnd"
        @click="finishRound()"
      />
    </v-card-actions>
  </v-card>
</template>

<script setup>
var user = defineModel("user");
var playerOut = defineModel("playerOut");
var lastChance = defineModel("lastChance");
var webSocket = defineModel("webSocket");
</script>

<script>
export default {
  data: () => ({
    lastChanceGuess: "",
    result: false,
    lastChanceEnd: false,

    lastChanceRules: [
      (value) => !!value || "Escribe una palabra",
      (value) => (value && value.length >= 2) || "Mínimo de 2 caracteres",
    ],
  }),

  beforeMount() {
    this.webSocketConfiguration();
  },

  methods: {
    webSocketConfiguration() {
      this.webSocket.addEventListener("message", (event) => {
        const messageData = JSON.parse(event.data);

        if (!("message_type" in messageData)) return;
        const messageType = messageData["message_type"];

        // Check only the possible lastChanceGuess messages
        if (messageType != "lastChanceGuess") return;

        this.result = JSON.parse(messageData["last_chance_guess"]);
        this.lastChanceEnd = true;
      });
    },

    lastChanceVote() {
      this.$refs.lastChanceVote.validate();
      if (!this.lastChanceGuess || this.lastChanceGuess.length < 2) return;

      this.webSocket.send(
        JSON.stringify({
          action: "lastChance",
          message: this.lastChanceGuess,
        })
      );
    },

    finishRound() {
      this.$router.push("/");
    },
  },
};
</script>
