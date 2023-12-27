<template>
  <v-container class="fill-height">
    <!-- LOBBY -->
    <v-responsive
      v-if="startedGame == false"
      class="align-center text-center fill-height"
    >
      <h1 style="font-size: 3rem; margin-top: 2rem; margin-bottom: 2rem">
        ~ Outsider ~
      </h1>

      <!-- Current players list -->
      <v-card variant="tonal" class="mx-auto text-left" max-width="300">
        <v-card-title style="margin-bottom: 0.5rem">
          <v-row>
            <v-col class="text-left">
              <b> Jugadores </b>
            </v-col>
            <v-col
              class="text-right"
              :style="{
                color:
                  currentUsers.length > 2 && currentUsers.length <= 5
                    ? 'white'
                    : 'black',
              }"
            >
              <b> {{ currentUsers.length }} / 5</b>
            </v-col>
          </v-row>
        </v-card-title>

        <v-list-item
          v-for="(item, i) in currentUsers"
          :key="i"
          :style="{ color: item.captain == true ? '#47ffda' : 'white' }"
        >
          - {{ item.username }}
          <v-icon v-if="item.captain" icon="mdi-crown-circle-outline"></v-icon>
          <v-icon v-if="item.id == user.id" icon="mdi-account-circle"></v-icon>
        </v-list-item>
      </v-card>

      <!-- Chat -->
      <v-card
        style="margin-top: 2rem; margin-bottom: 2rem"
        class="mx-auto"
        max-width="400"
      >
        <div id="chat" style="margin: 1.25rem">
          <div
            ref="chat"
            style="margin-bottom: 1rem"
            class="text-left"
            v-for="message in messages"
          >
            <b>{{ message.username }}</b> - {{ message.message }}
          </div>
        </div>

        <div>
          <form
            style="
              margin-bottom: 0.5rem;
              margin-left: 1.5rem;
              margin-right: 1.5rem;
            "
            ref="chatInput"
            @submit.prevent="handleMessageSubmit(username, text)"
          >
            <v-text-field
              class="mx-auto"
              v-model="text"
              placeholder="Mensaje"
              append-inner-icon="mdi-send"
              @click:append-inner="handleMessageSubmit(username, text)"
            ></v-text-field>
          </form>
        </div>
      </v-card>

      <!-- Room code -->
      <v-text-field
        :model-value="roomName"
        class="mx-auto text-left"
        style="width: 10rem"
        label="Código de sala"
        variant="outlined"
        readonly
      />

      <!-- Start game button -->
      <div>
        <v-btn
          style="margin-bottom: 2rem; margin-top: 1rem; margin-right: 1rem"
          :disabled="canStartGame()"
          @click="startGame()"
          class="text-none"
          prepend-icon="mdi-nintendo-game-boy"
          append-icon="mdi-check-circle-outline"
          rounded
        >
          Empezar partida
        </v-btn>
      </div>
    </v-responsive>

    <!-- GAME -->
    <v-responsive
      v-else="startedGame == false"
      class="align-center text-center fill-height"
    >
      <!-- PLayer role and given 'password' -->
      <h2 style="margin-bottom: 2rem">
        <v-icon icon="mdi-account-circle" /> {{ username }} ||
        <span style="color: #ffac2b" v-if="user.outsider">
          Outsider <v-icon icon="mdi-emoticon-devil-outline" />
        </span>
        <span style="color: #9cb443" v-else>
          Inocente <v-icon icon="mdi-emoticon-happy-outline" />
        </span>
        <p style="margin-top: 1rem">
          Contraseña:
          <span
            :style="{ color: user.outsider == true ? '#ffac2b' : '#47ffda' }"
            >{{ wordClue }}</span
          >
        </p>
      </h2>

      <!-- Actual turn interaction window -->
      <v-card
        style="margin-bottom: 2rem"
        variant="elevated"
        class="mx-auto"
        max-width="30rem"
        color="#545454"
      >
        <v-window
          disabled
          v-model="currentSlide"
          style="height: 100%; display: grid; align-content: center"
        >
          <v-form @submit.prevent ref="nextTurn">
            <v-window-item v-for="player in currentUsers">
              <v-sheet
                color="#545454"
                class="mx-auto"
                style="width: 25rem; padding-bottom: 1rem"
              >
                <!-- Header -->
                <div style="padding-top: 2rem">
                  <h2 v-if="!startedVoting">
                    Turno de:
                    <span style="color: #9cb443"> {{ player.username }}</span>
                  </h2>
                  <h2 v-else>
                    <v-chip
                      size="x-large"
                      append-icon="mdi-skull"
                      prepend-icon="mdi-skull"
                    >
                      Votaciones! - Elige al outsider del grupo
                    </v-chip>
                  </h2>
                </div>

                <v-divider
                  style="margin-top: 2rem; margin-bottom: 2rem"
                  :thickness="3"
                />

                <!-- Current users/words list -->
                <h2 class="h2-spacing">Palabras usadas:</h2>
                <v-list-item
                  style="margin-top: 1rem"
                  v-for="player in currentUsers"
                >
                  <h3>
                    <v-icon
                      v-if="player.id == user.id"
                      icon="mdi-account-circle"
                    />

                    {{ player.username }} -
                    <span style="color: #47ffda" v-if="player.guessWord">
                      {{ player.guessWord }}</span
                    >
                    <i v-else> No ha respondido </i>

                    <span v-if="startedVoting">
                      &nbsp
                      <v-btn
                        density="comfortable"
                        variant="outlined"
                        style="color: #ffc168"
                        prepend-icon="mdi-skull"
                        :rounded="true"
                        :loading="sendingVote"
                        @click="sendVote(player)"
                      >
                        Eliminar
                        <template v-slot:loader>
                          <v-progress-linear indeterminate></v-progress-linear>
                        </template>
                      </v-btn>
                    </span>
                  </h3>
                </v-list-item>

                <v-divider
                  style="margin-top: 2rem; margin-bottom: 2rem"
                  :thickness="3"
                />

                <!-- New word form -->
                <v-card color="#323232">
                  <v-text-field
                    class="mx-auto"
                    style="
                      width: 20rem;
                      margin-top: 1rem;
                      margin-bottom: 0.75rem;
                    "
                    v-model="newWord"
                    label="Hmmmmmm..."
                    clearable
                    @keydown.space.prevent
                    :rules="wordRules"
                    :disabled="!(user.state == 'PLAYER_TURN')"
                  />

                  <v-btn
                    v-if="!startedVoting"
                    class="text-none"
                    style="margin-bottom: 1rem"
                    @click="nextTurn()"
                    :rounded="true"
                    :disabled="!(user.state == 'PLAYER_TURN')"
                    nextTurn
                  >
                    Enviar
                  </v-btn>
                </v-card>
              </v-sheet>
            </v-window-item>
          </v-form>
        </v-window>
      </v-card>

      <!-- Player turn indicators -->
      <div v-if="!startedVoting">
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
          </h3>
        </div>

        <div v-else>
          <v-chip variant="flat" size="x-large">
            <v-icon start color="#ffac2b" icon="mdi mdi-circle" />
            <h2>Espera a tu turno...</h2>
          </v-chip>
        </div>
      </div>

      <!-- Repeated word dialogue -->
      <v-dialog max-width="22.5rem" v-model="repeatedWordDialog">
        <template v-slot:default="{ isActive }">
          <v-card color="#323232" title="Palabra repetida">
            <v-card-text>
              La palabra que intentas introducir está repetida, revisa la lista
              de palabras repetidas para continuar</v-card-text
            >
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
    </v-responsive>

    <!-- RESULTS -->
    <v-dialog v-model="showResults">
      <template v-slot:default="{ isActive }">
        <v-card color="#323232" title="Resultados">
          <v-card-text>
            <h3 v-if="playerOut">
              <span style="color: #47ffda">{{ playerOut.username }} </span>
              ha sido eliminado y era
              <span v-if="playerOut.outsider">
                <span style="color: #ffac2b"> outsider </span>
                por ello han ganado el resto de jugadores inocentes
                <v-icon
                  style="color: #9cb443"
                  icon="mdi-emoticon-happy-outline"
                />
              </span>
              <span v-else>
                <span style="color: #9cb443"> inocente </span>
                por ende ha ganado el jugador Outsider
                <v-icon
                  style="color: #ffac2b"
                  icon="mdi-emoticon-devil-outline"
                />
              </span>
            </h3>
            <h3 v-else>Empate en las votaciones. Nadie gana O.o</h3>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              style="margin: 0.5rem"
              variant="tonal"
              text="Terminar partida"
              rounded
              class="text-none"
              @click="finishRound()"
            ></v-btn>
          </v-card-actions>
        </v-card>
      </template>
    </v-dialog>
  </v-container>
</template>

<style>
#chat {
  display: flex;
  flex-direction: column;
  height: 10rem;
  overflow-y: scroll;
}
</style>

<script>
import axios from "axios";
import Constants from "../constants";

export default {
  data: () => ({
    window: 0,
    username: "",
    roomName: null,
    webSocket: null,
    messages: [],
    text: "",

    user: null,
    currentUsers: [],

    startedGame: false,

    wordClue: "",
    newWord: "",
    currentSlide: 0,
    repeatedWordDialog: false,

    startedVoting: false,
    sendingVote: false,

    showResults: false,
    playerOut: null,

    wordRules: [
      (value) => !!value || "Escribe una palabra",
      (value) => (value && value.length >= 2) || "Mínimo de 2 caracteres",
    ],

    canStartGame() {
      if (!this.currentUsers || !this.user) return true;
      return (
        !this.user.captain ||
        this.currentUsers.length <= 2 ||
        this.currentUsers.length > 5
      );
    },
  }),

  mounted() {
    // Check that the user has an username
    this.username = this.$store.state.userName;
    if (this.username.length == 0) {
      this.$router.push("/");
      return;
    }

    // Check if room exists
    const serverPath = Constants.API_URL + "logic/rooms/" + this.roomName + "/";
    axios.get(serverPath).catch((error) => {
      this.$router.push("/");
      return;
    });

    this.webSocketConfiguration();
  },

  created() {
    this.roomName = this.$route.params.roomName;
    window.addEventListener("beforeunload", function (event) {
      event.preventDefault();
    });
  },

  beforeRouteLeave(to, from, next) {
    // Websocket end connection
    if (this.webSocket) {
      this.webSocket.close();
    }
    next();
  },

  methods: {
    webSocketConfiguration() {
      console.log("Starting connection to websocket");

      this.webSocket = new WebSocket(
        Constants.WEBSOCKET_URL + "ws/room/" + this.roomName + "/"
      );

      this.webSocket.addEventListener("open", (event) => {
        const messageData = {
          action: "connection",
          username: this.username,
          message: "",
        };
        this.webSocket.send(JSON.stringify(messageData));
        console.log("Connection stablished");
      });

      this.webSocket.addEventListener("close", (event) => {
        console.log("Connection closed");
      });

      this.webSocket.addEventListener("message", (event) => {
        const messageData = JSON.parse(event.data);

        if (!("message_type" in messageData)) return;

        const messageType = messageData["message_type"];

        if (messageType == "startGame") {
          this.currentUsers = JSON.parse(messageData["actual_users"]);
          this.user = JSON.parse(messageData["user"]);
          this.startedGame = true;
          this.wordClue = messageData["key_word"];
          return;
        }

        if (messageType == "nextTurn") {
          if (this.currentSlide + 1 >= this.currentUsers.length) {
            // Ending round/game -> Voting phase
            this.startedVoting = true;
          } else this.currentSlide++;

          this.currentUsers = JSON.parse(messageData["actual_users"]);
          this.user = JSON.parse(messageData["user"]);
          return;
        }

        if (messageType == "votingOutsider") {
          this.sendResults(messageData["player_out"]);
          return;
        }

        if (messageType == "votingComplete") {
          // Check vote results
          const playerOut = messageData["player_out"];

          this.showResults = true;

          if (playerOut) {
            // Check the most voted player
            this.playerOut = playerOut;
          } else {
            // Else -> Tie detected
          }

          return;
        }

        // Update actual connections
        if (messageType == "connection" || messageType == "disconnection") {
          this.currentUsers = JSON.parse(messageData["actual_users"]);
          this.user = JSON.parse(messageData["user"]);
        }

        // Chat messages configuration
        this.messages.push(messageData);

        if (this.messages.length == 50) this.messages = [];

        this.$nextTick(function () {
          // nextTick -> DOM is now updated
          if (this.$refs.chat[this.$refs.chat.length - 1])
            this.$refs.chat[this.$refs.chat.length - 1].scrollIntoView({
              block: "nearest",
              behavior: "smooth",
            });
        });
      });
    },

    handleMessageSubmit(username, text) {
      if (text.length == 0) return;

      if (text.length >= 100) {
        this.text = "";
        alert("Evita spamear en el chat (づ ◕‿◕ )づ");

        return;
      }

      const messageData = { username: username, message: text };

      // Send the message data to the server using WebSockets
      this.webSocket.send(JSON.stringify(messageData));
      this.text = "";
    },

    startGame() {
      const messageData = {
        action: "startGame",
        message: "",
      };
      this.webSocket.send(JSON.stringify(messageData));
    },

    nextTurn() {
      this.$refs.nextTurn.validate();
      if (!this.newWord || this.newWord.length < 2) return;

      const words = this.currentUsers.map(({ guessWord }) => guessWord);
      if (words.indexOf(this.newWord) !== -1) {
        this.repeatedWordDialog = true;
        return;
      }

      const messageData = {
        action: "nextTurn",
        message: this.newWord,
        order: this.currentUsers,
      };

      this.webSocket.send(JSON.stringify(messageData));
    },

    sendVote(player) {
      this.sendingVote = true;

      const messageData = {
        action: "votingOutsider",
        message: player.id,
      };

      this.webSocket.send(JSON.stringify(messageData));
    },

    sendResults(playerOut) {
      // Vote completed -> Send results to all the player
      const messageData = {
        action: "votingComplete",
        message: playerOut,
      };
      this.webSocket.send(JSON.stringify(messageData));
    },

    finishRound() {
      location.reload();
    },
  },
};
</script>
