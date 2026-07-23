import { useState, useEffect, useCallback } from 'react';
import { voiceOutputService } from '../services/VoiceOutputService';
import { SpeechSettings } from '../types/speech';

export const useSpeechSynthesis = () => {
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [isSpeaking, setIsSpeaking] = useState(false);

  useEffect(() => {
    voiceOutputService.initialize();
    
    // Poll for voices if they are still loading (browser behavior)
    const checkVoices = setInterval(() => {
      const availableVoices = voiceOutputService.getAvailableVoices();
      if (availableVoices.length > 0) {
        setVoices(availableVoices);
        clearInterval(checkVoices);
      }
    }, 100);

    return () => {
      clearInterval(checkVoices);
    };
  }, []);

  const speak = useCallback((
    text: string, 
    settings: SpeechSettings,
    onStart?: () => void,
    onEnd?: () => void,
    onError?: () => void
  ) => {
    voiceOutputService.speak(
      text,
      settings,
      () => {
        setIsSpeaking(true);
        if (onStart) onStart();
      },
      () => {
        setIsSpeaking(false);
        if (onEnd) onEnd();
      },
      () => {
        setIsSpeaking(false);
        if (onError) onError();
      }
    );
  }, []);

  const stopSpeaking = useCallback(() => {
    voiceOutputService.cancel();
    setIsSpeaking(false);
  }, []);

  return {
    voices,
    isSpeaking,
    speak,
    stopSpeaking
  };
};
