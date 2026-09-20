import { Room, RoomEvent } from "livekit-client";

export const connectToRoom = async (url: string, token: string) => {
  const room = new Room();

  try {
    await room.connect(url, token);
    return room;
  } catch (error: any) {
    throw new Error(`Failed to connect to LiveKit room: ${error.message}`);
  }
};

export const setupAudioHandlers = (
  room: Room,
  audioElement: HTMLAudioElement | null
) => {
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
