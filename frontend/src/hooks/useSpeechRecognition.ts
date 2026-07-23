import { useState, useEffect, useRef, useCallback } from 'react';
import { speechService } from '../services/SpeechService';

export interface SpeechCallbacks {
  onStateChange: (state: 'idle' | 'listening' | 'recognizing') => void;
  onTranscript: (transcript: string) => void;
  onEnd: (transcript: string) => void;
  onError: (error: string) => void;
}

export const useSpeechRecognition = (
  language: string,
  callbacks: SpeechCallbacks
) => {
  const [isListening, setIsListening] = useState(false);
  
  // SINGLETON INSTANCE
  const recognitionRef = useRef<any>(null);
  
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const hardTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  const transcriptRef = useRef<string>('');

  // Use refs for callbacks to avoid stale closures inside event listeners
  const callbacksRef = useRef(callbacks);
  useEffect(() => {
    callbacksRef.current = callbacks;
  }, [callbacks]);

  const clearTimers = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    if (hardTimeoutRef.current) {
      clearTimeout(hardTimeoutRef.current);
      hardTimeoutRef.current = null;
    }
  }, []);

  // Initialize ONLY ONCE
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      console.error("Speech Recognition is not supported in this browser.");
      return;
    }

    // Only create once
    if (!recognitionRef.current) {
      console.log("Initializing SpeechRecognition instance...");
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;
      
      recognition.onstart = () => {
        console.log("Voice Started: recognition.onstart fired.");
        console.log("SpeechRecognition available. Current language:", recognition.lang);
        setIsListening(true);
        callbacksRef.current.onStateChange('listening');
      };

      recognition.onspeechstart = () => {
        console.log("Speech Started: recognition.onspeechstart fired.");
        callbacksRef.current.onStateChange('recognizing');
      };

      recognition.onspeechend = () => {
        console.log("Speech Ended: recognition.onspeechend fired.");
        recognition.stop();
      };

      recognition.onaudioend = () => {
        console.log("Audio Ended: recognition.onaudioend fired.");
      };

      recognition.onresult = (event: any) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        const currentTranscript = finalTranscript + interimTranscript;
        
        console.log("Transcript Updated:");
        console.log("  Interim:", interimTranscript);
        console.log("  Final:", finalTranscript);
        if (event.results[0] && event.results[0][0]) {
          console.log("  Confidence:", event.results[0][0].confidence);
        }

        transcriptRef.current = currentTranscript;
        callbacksRef.current.onTranscript(currentTranscript);

        // Reset silence timer
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
        }
        
        silenceTimerRef.current = setTimeout(() => {
          console.log("Silence Detected (1000ms). Stopping recognition...");
          recognition.stop();
        }, 1000); 
      };

      recognition.onnomatch = () => {
        console.warn("Recognition onnomatch fired.");
        callbacksRef.current.onError("I didn't catch that.");
      };

      recognition.onerror = (event: any) => {
        console.error(`Recognition error: ${event.error}`);
        if (event.error === 'not-allowed') {
          callbacksRef.current.onError('Microphone permission denied.');
        } else if (event.error === 'no-speech') {
          callbacksRef.current.onError("I didn't catch that.");
        } else if (event.error !== 'aborted') {
          callbacksRef.current.onError(`Speech recognition error: ${event.error}`);
        }
        clearTimers();
        setIsListening(false);
        callbacksRef.current.onStateChange('idle');
      };

      recognition.onend = () => {
        console.log("Recognition Ended: recognition.onend fired.");
        clearTimers();
        setIsListening(false);
        
        if (transcriptRef.current && transcriptRef.current.length > 1) {
          console.log("Sending transcript:", transcriptRef.current);
        } else {
          console.log("Empty transcript. Returning to idle.");
        }
        
        callbacksRef.current.onEnd(transcriptRef.current);
        transcriptRef.current = ''; 
      };

      recognitionRef.current = recognition;
    }

    // Update language dynamically if it changes
    if (recognitionRef.current.lang !== language) {
       recognitionRef.current.lang = language;
    }
    
    // We intentionally DO NOT return an abort cleanup function here.
    // React strict mode will unmount/remount this on load. If we abort, we break the singleton.
  }, [language, clearTimers]);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) {
      callbacksRef.current.onError('Voice is not supported in this browser.');
      console.error("Browser permission / HTTPS / localhost issue might exist. SpeechRecognition not initialized.");
      return;
    }
    
    try {
      console.log("Starting Recognition...");
      transcriptRef.current = '';
      callbacksRef.current.onTranscript('');
      recognitionRef.current.start();
      
      // Setup hard timeout of 15 seconds
      if (hardTimeoutRef.current) clearTimeout(hardTimeoutRef.current);
      hardTimeoutRef.current = setTimeout(() => {
        console.log("Hard timeout reached (15 seconds). Forcing stop.");
        if (recognitionRef.current) {
          recognitionRef.current.stop();
        }
      }, 15000);
      
    } catch (e) {
      console.warn("Error starting recognition:", e);
    }
  }, []);

  const stopListening = useCallback(() => {
    console.log("Manual Stop Clicked. Forcing recognition.stop()");
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      clearTimers();
    }
  }, [isListening, clearTimers]);
  
  const cancelListening = useCallback(() => {
    console.log("Manual Cancel Clicked. Forcing recognition.abort()");
    if (recognitionRef.current && isListening) {
      recognitionRef.current.abort();
      clearTimers();
      setIsListening(false);
      callbacksRef.current.onStateChange('idle');
    }
  }, [isListening, clearTimers]);

  return {
    isListening,
    startListening,
    stopListening,
    cancelListening
  };
};
