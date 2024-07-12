import { createStore } from "vuex";

export default createStore({
  state: {
    userName: "",
  },
  mutations: {
    setUserName(state, userName) {
        state.userName = userName;
    },
    removeUserName(state) {
        state.userName = "";
    },
  },
});
