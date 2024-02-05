<template>
  <!-- PLayer role and given 'password' -->
  <h2 style="margin-bottom: 2rem; margin-top: 1rem">
    <span v-if="user.captain"
      ><v-icon style="color: #47ffda" icon="mdi-crown-circle-outline" />
      -
    </span>

    <span v-if="user.state == State.OUT">
      <v-icon icon="mdi-account-circle" /> {{ user.username }} - Eliminado
      <v-icon icon="mdi-emoticon-confused-outline" />
      <p style="margin-top: 1rem">Contraseña: ???</p>
    </span>

    <span v-else>
      <v-icon icon="mdi-account-circle" /> {{ user.username }} //

      <v-hover>
        <template v-slot:default="{ isHovering, props }">
          <v-chip
            size="large"
            variant="outlined"
            v-bind="props"
            :ripple="false"
            :color="isHovering ? '#545454' : undefined"
            link
          >
            <h2>
              Revelar rol...
              <span v-if="isHovering">
                <span style="color: #ffac2b" v-if="user.outsider">
                  Outsider
                  <v-icon size="small" icon="mdi-emoticon-devil-outline" />
                </span>
                <span style="color: #9cb443" v-else>
                  Inocente
                  <v-icon size="small" icon="mdi-emoticon-happy-outline" />
                </span>
              </span>
            </h2>
          </v-chip>
        </template>
      </v-hover>

      <p style="margin-top: 1rem">
        <v-hover>
          <template v-slot:default="{ isHovering, props }">
            <v-chip
              size="large"
              variant="elevated"
              v-bind="props"
              :ripple="false"
              link
            >
              <h2>
                Contraseña...
                <span v-if="isHovering">
                  <span
                    :style="{
                      color: user.outsider == true ? '#ffac2b' : '#47ffda',
                    }"
                  >
                    {{ wordClue }}
                  </span>
                </span>
              </h2>
            </v-chip>
          </template>
        </v-hover>
      </p>
    </span>
  </h2>
</template>

<script setup>
var user = defineModel("user");
var wordClue = defineModel("wordClue");
</script>

<script>
import Constants from "../constants";
var State = Constants.State;
</script>
