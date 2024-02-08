<template>
  <h1 style="font-size: 3rem; margin-top: 2rem; margin-bottom: 2rem">
    ~ Outsider ~
  </h1>

  <!-- Current players list -->
  <v-card variant="tonal" class="mx-auto text-left" max-width="375">
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
          <span v-if="currentUsers.length >= 6 && currentUsers.length <= 8">
            (2 Outsiders)
          </span>
        </v-col>
      </v-row>
    </v-card-title>

    <v-list-item
      v-for="(player, i) in currentUsers"
      :key="i"
      :style="{ color: player.captain == true ? '#47ffda' : 'white' }"
    >
      - {{ player.username }}
      <v-icon v-if="player.captain" icon="mdi-crown-circle-outline"></v-icon>
      <v-icon v-if="player.id == user.id" icon="mdi-account-circle"></v-icon>
    </v-list-item>
  </v-card>

  <ChatComponent
    style="margin-top: 1rem"
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
</template>

<script setup>
import ChatComponent from "@/components/ChatComponent.vue";

var roomName = defineModel("roomName");
var user = defineModel("user");
var username = defineModel("username");
var currentUsers = defineModel("currentUsers");
var messages = defineModel("messages");
var webSocket = defineModel("webSocket");
</script>

<script>
export default {
  data: () => ({
    canStartGame() {
      if (!this.currentUsers || !this.user) return true;
      return (
        !this.user.captain ||
        this.currentUsers.length <= 2 ||
        this.currentUsers.length > 8
      );
    },
  }),

  methods: {
    startGame() {
      this.webSocket.send(
        JSON.stringify({
          action: "startGame",
          message: "",
        })
      );
    },
  },
};
</script>
