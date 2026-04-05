"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * useSTT — Speech-to-Text hook.
 *
 * Uses the Web Speech API (Chrome/Edge) for real-time transcription.
 * Falls back to recording + backend /voice/transcribe for unsupported browsers.
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type SpeechRecognitionType = any;

export function useSTT() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [supported, setSupported] = useState(false);
  const recognitionRef = useRef<SpeechRecognitionType>(null);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    /* eslint-disable @typescript-eslint/no-explicit-any */
    const SR =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;
    setSupported(!!SR);
  }, []);

  const startListening = useCallback(() => {
    /* eslint-disable @typescript-eslint/no-explicit-any */
    const SR =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (SR) {
      // Use Web Speech API
      const recognition = new SR();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = "en-US";
      recognition.maxAlternatives = 1;

      recognition.onresult = (event: any) => {
        let final = "";
        let interim = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const text = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            final += text;
          } else {
            interim += text;
          }
        }
        setTranscript(final || interim);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognition.onerror = (event: any) => {
        console.warn("STT error:", event.error);
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
      setIsListening(true);
      setTranscript("");
    } else {
      // Fallback: record audio and send to backend
      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then((stream) => {
          const recorder = new MediaRecorder(stream, {
            mimeType: MediaRecorder.isTypeSupported("audio/webm")
              ? "audio/webm"
              : "audio/mp4",
          });
          chunksRef.current = [];
          recorder.ondataavailable = (e) => {
            if (e.data.size > 0) chunksRef.current.push(e.data);
          };
          recorder.onstop = async () => {
            stream.getTracks().forEach((t) => t.stop());
            const blob = new Blob(chunksRef.current, { type: "audio/webm" });
            const form = new FormData();
            form.append("audio", blob, "clip.webm");
            try {
              const res = await fetch("http://127.0.0.1:8000/voice/transcribe", {
                method: "POST",
                body: form,
              });
              if (res.ok) {
                const data = await res.json();
                setTranscript(data.text || "");
              }
            } catch {
              console.warn("Backend STT failed");
            }
            setIsListening(false);
          };
          mediaRef.current = recorder;
          recorder.start();
          setIsListening(true);
          setTranscript("");
        })
        .catch(() => {
          console.warn("Microphone access denied");
          setIsListening(false);
        });
    }
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    if (mediaRef.current && mediaRef.current.state !== "inactive") {
      mediaRef.current.stop();
      mediaRef.current = null;
    }
    setIsListening(false);
  }, []);

  const clearTranscript = useCallback(() => {
    setTranscript("");
  }, []);

  return {
    startListening,
    stopListening,
    clearTranscript,
    transcript,
    isListening,
    supported,
  };
}
