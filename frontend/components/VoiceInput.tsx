"use client";

import { useState } from "react";

import { api } from "../lib/api";

export default function VoiceInput({ onText }: { onText: (text: string) => void }) {
  const [listening, setListening] = useState(false);
  const [error, setError] = useState<string>("");
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);

  const start = async () => {
    try {
      setError("");
      if (!navigator.mediaDevices?.getUserMedia) {
        setError("Microphone is not supported in this browser.");
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: BlobPart[] = [];

      recorder.ondataavailable = (event: BlobEvent) => {
        if (event.data && event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      recorder.onerror = () => {
        setError("Unable to record audio.");
        setListening(false);
      };

      recorder.onstop = async () => {
        setListening(false);
        stream.getTracks().forEach((track) => track.stop());
        try {
          const blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
          const file = new File([blob], "recording.webm", { type: blob.type || "audio/webm" });
          const response = await api.transcribeAudio(file);
          onText(response?.text || "");
        } catch {
          setError("Transcription failed.");
        }
      };

      recorder.start();
      setMediaRecorder(recorder);
      setListening(true);
    } catch {
      setError("Microphone permission denied or unavailable.");
      setListening(false);
    }
  };

  const stop = () => {
    mediaRecorder?.stop();
  };

  return (
    <div className="flex items-center gap-2">
      <button className="btn-secondary" onClick={listening ? stop : start} type="button">
        {listening ? "Stop recording" : "Voice input"}
      </button>
      {error ? <p className="text-xs text-red-700">{error}</p> : null}
    </div>
  );
}
