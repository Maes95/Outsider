<template>
  <!-- Disconnection dialog -->
  <DisconnectionDialog v-model:disconnection="disconnection" />

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
                  currentUsers.length > 2 && currentUsers.length <= 8
                    ? '#47ffda'
                    : '#ffac2b',
              }"
            >
              <b> {{ currentUsers.length }} / 8</b>
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
      <ChatComponent
        ref="chat"
        v-model:username="username"
        v-model:messages="messages"
        v-model:webSocket="webSocket"
      />

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
      <v-btn
        style="margin-top: 1rem; margin-bottom: 2rem; margin-right: 1rem"
        :disabled="canStartGame()"
        @click="startGame()"
        class="text-none"
        prepend-icon="mdi-nintendo-game-boy"
        append-icon="mdi-check-circle-outline"
        rounded
      >
        Empezar partida
      </v-btn>
    </v-responsive>

    <!-- GAME -->
    <v-responsive
      v-else="startedGame == false"
      class="align-center text-center fill-height"
    >
      <!-- PLayer role and given 'password' -->
      <h2 style="margin-bottom: 2rem; margin-top: 1rem">
        <v-icon
          style="color: #47ffda"
          v-if="user.captain"
          icon="mdi-crown-circle-outline"
        />
        -
        <span v-if="user.state == State.OUT">
          <v-icon icon="mdi-account-circle" /> {{ username }} - Eliminado
          <v-icon icon="mdi-emoticon-confused-outline" />
          <p style="margin-top: 1rem">Contraseña: ???</p>
        </span>
        <span v-else>
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
        </span>
      </h2>

      <!-- Turn information and chat -->
      <v-row style="max-width: 60rem" class="mx-auto">
        <!-- Actual turn interaction window -->
        <v-col>
          <v-card
            style="margin-bottom: 2rem"
            variant="elevated"
            color="#545454"
          >
            <v-window disabled v-model="currentSlide">
              <v-form @submit.prevent ref="nextTurn">
                <v-window-item v-for="player in currentUsers">
                  <v-sheet color="#545454" style="padding-bottom: 1rem">
                    <!-- Header -->
                    <div style="padding-top: 2rem">
                      <h2 v-if="!startedVoting">
                        Turno de:
                        <span style="color: #47ffda">
                          {{ player.username }}</span
                        >
                      </h2>
                      <h2 v-else>
                        <v-chip
                          size="x-large"
                          append-icon="mdi-skull"
                          prepend-icon="mdi-skull"
                        >
                          Elige al outsider del grupo</v-chip
                        >
                      </h2>
                    </div>

                    <v-divider
                      style="margin-top: 2rem; margin-bottom: 2rem"
                      :thickness="3"
                    />

                    <!-- Current players/words list -->
                    <h2 class="h2-spacing">Palabras usadas:</h2>
                    <v-list-item
                      style="margin-top: 1rem"
                      v-for="player in currentPlayers"
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
                            :disabled="user.state == State.OUT"
                            :rounded="true"
                            :loading="sendingVote"
                            @click="sendVote(player)"
                          >
                            Eliminar
                            <template v-slot:loader>
                              <v-progress-linear indeterminate />
                            </template>
                          </v-btn>
                        </span>
                      </h3>
                    </v-list-item>

                    <v-divider
                      v-if="eliminatedPlayers.length"
                      style="margin-top: 2rem; margin-bottom: 2rem"
                      :thickness="3"
                    />

                    <!-- Eliminated players list -->
                    <v-list-item
                      style="color: #323232"
                      v-for="player in eliminatedPlayers"
                    >
                      <h3>
                        <v-icon
                          v-if="player.id == user.id"
                          icon="mdi-account-circle"
                        />

                        <i> {{ player.username }} - Eliminado </i>
                      </h3>
                    </v-list-item>

                    <v-divider
                      style="margin-top: 2rem; margin-bottom: 2rem"
                      :thickness="3"
                    />

                    <!-- New word form -->
                    <v-card
                      style="margin-left: 1rem; margin-right: 1rem"
                      color="#323232"
                    >
                      <v-text-field
                        class="mx-auto"
                        style="
                          margin-top: 1rem;
                          margin-bottom: 0.75rem;
                          padding-left: 2rem;
                          padding-right: 2rem;
                        "
                        v-model="newWord"
                        label="Hmmmmmm..."
                        clearable
                        @keydown.space.prevent
                        :rules="wordRules"
                        :disabled="!(user.state == State.PLAYER_TURN)"
                      />

                      <v-btn
                        v-if="!startedVoting"
                        class="text-none"
                        style="margin-bottom: 1rem"
                        @click="nextTurn()"
                        :rounded="true"
                        :disabled="!(user.state == State.PLAYER_TURN)"
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
        </v-col>

        <!-- Chat and player turn indicators-->
        <v-col v-if="showChat">
          <ChatComponent
            style="margin-top: 2rem"
            ref="chat"
            v-model:username="username"
            v-model:messages="messages"
            v-model:webSocket="webSocket"
          />

          <div v-if="!startedVoting" style="margin-top: 6rem">
            <TurnIndicatorComponent v-model:user="user" />
          </div>
        </v-col>
      </v-row>

      <!-- Player turn indicators -->
      <div v-if="!showChat && !startedVoting" style="margin-bottom: 1rem">
        <TurnIndicatorComponent v-model:user="user" />
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
    <v-dialog persistent max-width="700" width="auto" v-model="showResults">
      <ResultsComponent
        v-model:showResults="showResults"
        v-model:user="user"
        v-model:playerOut="playerOut"
        v-model:lastChance="lastChance"
        v-model:lastChanceEnd="lastChanceEnd"
        v-model:webSocket="webSocket"
        v-model:continuePlaying="continuePlaying"
      />
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

<script setup>
import ChatComponent from "@/components/ChatComponent.vue";
import TurnIndicatorComponent from "@/components/TurnIndicatorComponent.vue";
import DisconnectionDialog from "@/components/DisconnectionDialog.vue";
import ResultsComponent from "@/components/ResultsComponent.vue";
</script>

<script>
import axios from "axios";
import Constants from "../constants";

const State = {
  LOBBY: "LOBBY",
  PLAYING: "PLAYING",
  PLAYER_TURN: "PLAYER_TURN",
  OUT: "OUT",
};

export default {
  data: () => ({
    // General variables
    user: null,
    username: "",
    roomName: null,
    webSocket: 0,
    currentUsers: [],
    eliminatedPlayers: [],
    currentPlayers: [],
    disconnection: false,

    // Chat variables
    messages: [],
    showChat: false,

    // Game variables
    startedGame: false,
    wordClue: "",
    newWord: "",
    currentSlide: 0,
    repeatedWordDialog: false,

    // Results variables
    startedVoting: false,
    sendingVote: false,
    showResults: false,
    playerOut: null,
    lastChance: false,
    lastChanceEnd: false,
    lastChanceWord: "",
    continuePlaying: true,

    wordRules: [
      (value) => !!value || "Escribe una palabra",
      (value) => (value && value.length >= 2) || "Mínimo de 2 caracteres",
      (value) => (value && value.length < 16) || "Palabra demasiado larga",
    ],

    canStartGame() {
      if (!this.currentUsers || !this.user) return true;
      return (
        !this.user.captain ||
        this.currentUsers.length <= 2 ||
        this.currentUsers.length > 8
      );
    },
  }),

  beforeMount() {
    // Check that the user has an username
    this.username = this.$store.state.userName;
    if (this.username.length == 0) {
      this.$router.push("/");
      return;
    }

    // Check if room exists
    const serverPath = Constants.API_URL + "logic/rooms/" + this.roomName + "/";
    axios
      .get(serverPath)
      .then((response) => {
        if (response.data.started_game) {
          this.$router.push("/");
          return;
        }
      })
      .catch((error) => {
        this.$router.push("/");
        return;
      });

    this.webSocketConfiguration();
  },

  created() {
    this.showChat = !this.isMobile(); // Show in-game chat if not mobile
    this.roomName = this.$route.params.roomName;

    /*
    window.addEventListener("beforeunload", function (event) {
      event.preventDefault();
    });
    */
  },

  beforeUnmount() {
    // Close webSocket before leaving
    if (this.webSocket) {
      this.webSocket.close();
    }
  },

  methods: {
    isMobile() {
      if (/Android|iPhone/i.test(navigator.userAgent)) {
        return true;
      } else if (screen.width < 1024) {
        return true;
      } else {
        return false;
      }
    },

    filterPlayers(users) {
      return users.filter(
        (player) =>
          player.state == State.PLAYING || player.state == State.PLAYER_TURN
      );
    },

    filterPlayersInverse(users) {
      return users.filter((player) => player.state == State.OUT);
    },

    webSocketConfiguration() {
      console.log("Starting connection to websocket");

      this.webSocket = new WebSocket(
        Constants.WEBSOCKET_URL + "ws/room/" + this.roomName + "/"
      );

      this.webSocket.addEventListener("open", (event) => {
        this.webSocket.send(
          JSON.stringify({
            action: "connection",
            username: this.username,
            message: "",
          })
        );
        console.log("Connection stablished");
      });

      this.webSocket.addEventListener("close", (event) => {
        console.log("Connection closed");
      });

      this.webSocket.addEventListener("message", (event) => {
        const messageData = JSON.parse(event.data);

        if (!("message_type" in messageData)) return;
        const messageType = messageData["message_type"];

        this.messageListener(messageData, messageType);
      });
    },

    messageListener(messageData, messageType) {
      console.log(messageType);

      switch (messageType) {
        case "connection":
        case "disconnection":
          let checkUsers = JSON.parse(messageData["actual_users"]);
          let filteredPlayers = this.filterPlayers(checkUsers);

          this.user = JSON.parse(messageData["user"]);

          if (messageType == "disconnection") {
            let disconnectedUser = messageData["disconnected_user"];

            console.log(disconnectedUser);

            // Check disconnections of PLAYERS (Ignore spectators) during rounds
            if (
              this.startedGame &&
              this.continuePlaying &&
              (disconnectedUser.state != State.OUT ||
                (this.lastChance && !this.lastChanceEnd))
            ) {
              this.disconnection = true;
              this.webSocket.send(
                JSON.stringify({
                  action: "endGame",
                  message: "",
                })
              );
              return;
            }

            if (
              this.showResults &&
              (disconnectedUser.state == State.OUT || !this.continuePlaying)
            ) {
              return;
            }
          }

          this.currentUsers = checkUsers;
          this.currentPlayers = filteredPlayers;
          this.eliminatedPlayers = this.filterPlayersInverse(this.currentUsers);

          break;

        case "startGame":
          this.currentUsers = JSON.parse(messageData["actual_users"]);
          this.currentPlayers = this.filterPlayers(this.currentUsers);
          this.user = JSON.parse(messageData["user"]);

          this.startedGame = true;
          this.wordClue = messageData["key_word"];
          return;

        case "nextTurn":
          if (this.currentSlide + 1 >= this.currentPlayers.length) {
            // Ending round/game -> Voting phase
            this.startedVoting = true;
          } else this.currentSlide++;

          this.currentUsers = JSON.parse(messageData["actual_users"]);
          this.currentPlayers = this.filterPlayers(this.currentUsers);
          this.user = JSON.parse(messageData["user"]);
          return;

        case "votingComplete":
          // Check vote results
          var playerOut = messageData["player_out"];

          this.showResults = true;
          this.currentUsers = JSON.parse(messageData["actual_users"]);
          this.continuePlaying = messageData["continue_playing"];

          if (playerOut) {
            // Check the most voted player
            this.playerOut = playerOut;
            this.lastChance = playerOut.outsider;
          } else {
            // Else -> Tie detected
          }
          return;

        case "lastChanceGuess":
          this.lastChanceEnd = true;
          this.continuePlaying = false;
          return;

        case "nextRound":
          this.currentUsers = JSON.parse(messageData["actual_users"]);
          this.currentPlayers = this.filterPlayers(this.currentUsers);
          this.eliminatedPlayers = this.filterPlayersInverse(this.currentUsers);
          this.user = JSON.parse(messageData["user"]);

          this.startedGame = true;
          this.currentSlide = 0;
          this.$refs.nextTurn.reset();
          this.wordClue = messageData["key_word"];

          this.showResults = false;
          this.startedVoting = false;
          this.sendingVote = false;
          this.playerOut = null;
          this.lastChance = false;
          this.lastChanceEnd = false;
          this.lastChanceWord = "";
          return;

        case "endGame":
          if (this.webSocket) {
            this.webSocket.close();
          }
          if (!this.disconnection) this.$router.push("/");
          return;
      }

      // Chat messages configuration
      this.messages.push(messageData);
      if (this.messages.length == 50) this.messages = [];
    },

    startGame() {
      this.webSocket.send(
        JSON.stringify({
          action: "startGame",
          message: "",
        })
      );
    },

    nextTurn() {
      this.$refs.nextTurn.validate();
      if (!this.newWord || this.newWord.length < 2 || this.newWord.length > 16)
        return;

      const words = this.currentPlayers.map(({ guessWord }) => guessWord);
      if (words.indexOf(this.newWord) !== -1) {
        this.repeatedWordDialog = true;
        return;
      }

      this.webSocket.send(
        JSON.stringify({
          action: "nextTurn",
          message: this.newWord,
          order: this.currentPlayers,
        })
      );
    },

    sendVote(player) {
      this.sendingVote = true;

      this.webSocket.send(
        JSON.stringify({
          action: "votingOutsider",
          message: player.id,
        })
      );
    },
  },
};
</script>
