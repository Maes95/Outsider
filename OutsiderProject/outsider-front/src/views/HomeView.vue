<template>
  <v-container class="fill-height">
    <v-responsive class="align-center text-center fill-height">
      <!-- How to play -->
      <v-row class="d-flex justify-end">
        <HowToPlayDialog class="d-none d-lg-block" style="margin-top: 1rem" />
      </v-row>

      <!-- Title -->
      <h1 style="font-size: 3rem; margin-top: 3rem; margin-bottom: 5rem">
        ~ Outsider ~
      </h1>

      <!-- Start/Join form -->
      <v-form @submit.prevent ref="start">
        <!-- Username input -->
        <v-row class="d-flex justify-center" style="margin-bottom: 5rem">
          <v-col cols="auto">
            <v-text-field
              v-model="userName"
              :rules="usernameRules"
              label="Nombre de jugador"
              prepend-icon="mdi-account"
              clearable
              style="width: 15rem"
            />
          </v-col>
        </v-row>

        <!-- Start/Join a game -->
        <div style="margin-bottom: 6rem">
          <v-row class="d-flex align-center justify-center">
            <v-col cols="auto">
              <v-text-field
                v-model="roomCode"
                style="width: 15rem"
                label="Código de sala"
                variant="outlined"
                :rules="gameCodeRules"
              ></v-text-field>
            </v-col>
          </v-row>

          <v-row class="d-flex align-center justify-center">
            <v-col cols="auto">
              <v-btn
                @click="joinRoom((create = true))"
                class="text-none"
                rounded
              >
                <v-icon icon="mdi-plus-circle" size="large" start />
                Crear sala
              </v-btn>
            </v-col>

            <v-col cols="auto">
              <v-btn @click="joinRoom()" class="text-none" rounded>
                <v-icon icon="mdi-account-multiple" size="large" start />
                Unirse
              </v-btn>
            </v-col>
          </v-row>
        </div>

        <!-- Try again dialogue -->
        <v-dialog max-width="25rem" v-model="errorDialog">
          <template v-slot:default="{ isActive }">
            <v-card color="#323232" title="Código no válido">
              <v-card-text> {{ errorDialogText }}</v-card-text>
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
      </v-form>

      <!-- How to play -->
      <v-row class="d-flex justify-center">
        <HowToPlayDialog class="d-lg-none" style="margin-bottom: 1rem" />
      </v-row>

      <!-- Github -->
      <v-row class="d-flex justify-center">
        <v-col cols="auto">
          <v-btn
            href="https://github.com/Javiex7/Outsider"
            target="_blank"
            class="text-none"
            rounded
            variant="plain"
            prepend-icon="mdi-github"
          >
            Outsider by Javiex7
          </v-btn>
        </v-col>
      </v-row>
    </v-responsive>
  </v-container>
</template>

<script setup>
import HowToPlayDialog from "@/components/HowToPlayDialog.vue";
</script>

<script>
import axios from "axios";
import Constants from "../constants";

export default {
  data: () => ({
    userName: "",
    roomCode: "",
    usernameRules: [
      (value) => !!value || "Nombre obligatorio",
      (value) => (value && value.length >= 5) || "Mínimo de 5 caracteres",
    ],
    gameCodeRules: [(value) => !!value || "Introduce un código válido"],
    errorDialog: false,
    errorDialogText: "Error inesperado",
  }),

  mounted() {
    this.userName = this.$store.state.userName;
  },

  methods: {
    async joinRoom(create = false) {
      const { valid } = await this.$refs.start.validate();
      if (!valid) return;

      this.roomCode = this.roomCode.trim();

      var serverPath;
      const routerPath = "/rooms/" + this.roomCode;

      // Save 'username' in the store
      this.$store.commit("setUserName", this.userName);

      if (create) {
        const formData = {
          name: this.roomCode,
        };

        serverPath = Constants.API_URL + "logic/rooms/";

        axios
          .post(serverPath, formData)
          .then((response) => {
            this.$router.push({ path: routerPath });
          })
          .catch((error) => {
            if (!error.response || error.response.status != 302) {
              this.errorDialog = true;
              return;
            }

            if (error.response.status == 302) {
              this.errorDialogText =
                "Ese código de sala ya está en uso, prueba uno diferente o únete como jugador.";
              this.errorDialog = true;
            }
          });

        return;
      }

      serverPath = Constants.API_URL + "logic/rooms/" + this.roomCode + "/";

      axios
        .get(serverPath)
        .then((response) => {
          this.$router.push({ path: routerPath });
        })
        .catch((error) => {
          if (!error.response || error.response.status != 404) {
            this.errorDialog = true;
            return;
          }

          if (error.response.status == 404) {
            this.errorDialogText =
              "Ese código NO está en uso, prueba con uno diferente o crea una sala.";
            this.errorDialog = true;
          }
        });
    },
  },
};
</script>
