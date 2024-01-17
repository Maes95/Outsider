<template>
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
        style="margin-bottom: 0.5rem; margin-left: 1.5rem; margin-right: 1.5rem"
        ref="chatInput"
        @submit.prevent="handleChatSubmit(username, chatText)"
      >
        <v-text-field
          class="mx-auto"
          v-model="chatText"
          placeholder="Mensaje"
          append-inner-icon="mdi-send"
          @click:append-inner="handleChatSubmit(username, chatText)"
        ></v-text-field>
      </form>
    </div>
  </v-card>
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
var messages = defineModel("messages");
var username = defineModel("username");
var webSocket = defineModel("webSocket");
</script>

<script>
export default {
  data: () => ({
    chatText: null,
  }),

  beforeMount() {
    if (!this.webSocket) return;
    this.webSocketConfiguration();
  },

  methods: {
    handleChatSubmit(username, chatText) {
      if (chatText.length == 0) return;

      if (chatText.length >= 100) {
        this.chatText = "";
        alert("Evita spamear en el chat (づ ◕‿◕ )づ");

        return;
      }

      this.webSocket.send(
        JSON.stringify({
          action: "default",
          message: chatText,
          username: username,
        })
      );
      this.chatText = "";
    },

    webSocketConfiguration() {
      this.webSocket.addEventListener("message", (event) => {
        const messageData = JSON.parse(event.data);

        if (!("message_type" in messageData)) return;
        const messageType = messageData["message_type"];

        // Check only chat/default messages
        if (messageType != "default") return;

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
  },
};
</script>
