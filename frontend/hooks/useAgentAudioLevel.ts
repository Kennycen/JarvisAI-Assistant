"use client";

import { useEffect, useRef } from "react";

/**
 * Taps the agent's audio track with an AnalyserNode and writes a 0..1 amplitude
 * into a ref, once per frame.
 *
 * A ref rather than state: this updates 60x/second and routing it through
 * useState would re-render the whole HUD every frame.
 */

const FFT_SIZE = 2048;

/**
 * Only the low bins carry speech. At 48kHz with fftSize 2048 each bin spans
 * ~23Hz, so bin 1023 sits at 24kHz and the top ~80% of the spectrum is silent
 * during conversation. The original openclaw code averaged all 1024 bins, which
 * diluted a talking voice by roughly 6x and left the orb nearly still.
 */
const SPEECH_BINS = 256; // ~0-6kHz

export interface AudioLevelOptions {
  /** Scales the final value. 1 is raw; the default suits normal speech. */
  sensitivity?: number;
  /** Extra frame-to-frame smoothing on top of the analyser's own. 0..1, higher is smoother. */
  smoothing?: number;
}

/**
 * Measured against Gemini's native-audio output: at 9 the level pinned to ~0.96
 * and clipped against the shader's 0..1 ceiling, flattening the orb's dynamics.
 * 5 puts speech peaks around 0.5 and leaves headroom.
 */
const DEFAULT_SENSITIVITY = 5;

export function useAgentAudioLevel(
  track: MediaStreamTrack | undefined,
  { sensitivity = DEFAULT_SENSITIVITY, smoothing = 0.35 }: AudioLevelOptions = {},
) {
  const levelRef = useRef(0);
  // Shared with the spectrum panel so it doesn't need a second AnalyserNode on
  // the same track.
  const binsRef = useRef<Uint8Array>(new Uint8Array(FFT_SIZE / 2));

  useEffect(() => {
    if (!track) {
      levelRef.current = 0;
      binsRef.current.fill(0);
      return;
    }

    const ctx = new AudioContext();
    const analyser = ctx.createAnalyser();
    analyser.fftSize = FFT_SIZE;
    analyser.smoothingTimeConstant = 0.8;

    const source = ctx.createMediaStreamSource(new MediaStream([track]));
    source.connect(analyser);
    // Intentionally NOT connected to ctx.destination: RoomAudioRenderer owns
    // playback, and connecting here too would play everything twice.
    //
    // Chrome caveat: a remote WebRTC track feeds silence into Web Audio unless
    // the same track is also attached to a live HTMLAudioElement somewhere.
    // RoomAudioRenderer does that, so it must stay mounted or this reads zero.

    // An AudioContext starts suspended without a user gesture.
    void ctx.resume().catch(() => {});

    const bins = new Uint8Array(analyser.frequencyBinCount);
    binsRef.current = bins;
    const usableBins = Math.min(SPEECH_BINS, analyser.frequencyBinCount);
    let raf = 0;

    const tick = () => {
      analyser.getByteFrequencyData(bins);
      let sum = 0;
      for (let i = 0; i < usableBins; i++) sum += bins[i];
      const raw = (sum / usableBins / 255) * (sensitivity / 5);
      levelRef.current =
        levelRef.current * smoothing + raw * (1 - smoothing);
      raf = requestAnimationFrame(tick);
    };
    tick();

    return () => {
      cancelAnimationFrame(raf);
      source.disconnect();
      analyser.disconnect();
      // Closing matters: browsers cap concurrent AudioContexts, and without
      // this every hot reload strands one.
      void ctx.close().catch(() => {});
      levelRef.current = 0;
    };
  }, [track, sensitivity, smoothing]);

  return { levelRef, binsRef };
}
