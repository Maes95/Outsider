const BASE_URL = "";
// const API_URL = "http://192.168.0.16:8000/";
const API_URL = "http://192.168.1.13:8000/";
// const WEBSOCKET_URL = "ws://192.168.0.16:8000/";
const WEBSOCKET_URL = "ws://192.168.1.13:8000/";

const State = {
  LOBBY: "LOBBY",
  PLAYING: "PLAYING",
  PLAYER_TURN: "PLAYER_TURN",
  OUT: "OUT",
};

export default {
  BASE_URL: BASE_URL,
  API_URL: API_URL,
  WEBSOCKET_URL: WEBSOCKET_URL,
  State: State,
};
