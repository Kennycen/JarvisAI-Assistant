import { Room, RoomEvent } from "livekit-client";

export const connectToRoom = async (url, token) => {
  const room = new Room();

  try {
    await room.connect(url, token);
    return room;
  } catch (error) {
    throw new Error(`Failed to connect to LiveKit room: ${error.message}`);
  }
};

export const setupAudioHandlers = (room, audioElement) => {
  if (!audioElement) return;

  room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
    if (track.kind === "audio") {
      track.attach(audioElement);
    }
  });

  room.on(RoomEvent.TrackUnsubscribed, (track) => {
    track.detach();
  });
};
