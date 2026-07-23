export type VoiceState = 'idle' | 'listening' | 'recognizing' | 'sending' | 'waiting_response' | 'speaking' | 'error';

export interface SpeechSettings {
  language: string;
  autoSpeak: boolean;
  voiceURI: string | null;
  pitch: number;
  rate: number;
  volume: number;
}

export const DEFAULT_SPEECH_SETTINGS: SpeechSettings = {
  language: 'en-US',
  autoSpeak: false,
  voiceURI: null,
  pitch: 1,
  rate: 1,
  volume: 1,
};

export const SUPPORTED_LANGUAGES = [
  { code: 'en-US', name: 'English (US)' },
  { code: 'en-IN', name: 'English (India)' },
  { code: 'hi-IN', name: 'Hindi (India)' },
];
