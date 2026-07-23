import { SpeechSettings } from '../types/speech';

export class VoiceOutputService {
  private voices: SpeechSynthesisVoice[] = [];
  private isInitialized = false;

  private static instance: VoiceOutputService;

  private constructor() {}

  public static getInstance(): VoiceOutputService {
    if (!VoiceOutputService.instance) {
      VoiceOutputService.instance = new VoiceOutputService();
    }
    return VoiceOutputService.instance;
  }

  public initialize() {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      console.error("Voice playback is not supported by this browser.");
      return;
    }

    if (this.isInitialized) return;

    this.loadVoices();
    window.speechSynthesis.onvoiceschanged = () => {
      this.loadVoices();
    };
    
    this.isInitialized = true;
  }

  public loadVoices() {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    this.voices = window.speechSynthesis.getVoices();
    if (this.voices.length > 0) {
      console.log(`Loaded ${this.voices.length} Voices`);
    }
  }

  public unlock() {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    // Speak an empty string with 0 volume to unlock the audio engine on user gesture
    const utterance = new SpeechSynthesisUtterance('');
    utterance.volume = 0;
    window.speechSynthesis.speak(utterance);
    this.isInitialized = true;
  }

  private stripMarkdown(text: string): string {
    return text
      .replace(/#+\s/g, '') // Remove headers
      .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold
      .replace(/\*(.*?)\*/g, '$1') // Remove italic
      .replace(/_(.*?)_/g, '$1') // Remove italic
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Extract text from links
      .replace(/\|/g, '') // Remove table pipes
      .replace(/```[\s\S]*?```/g, 'Code block omitted.') // Remove code blocks
      .replace(/`([^`]+)`/g, '$1') // Remove inline code
      .replace(/---/g, '') // Remove horizontal rules
      .replace(/📍 \*\*(.*?)\*\*(?:\r?\n){2,}/, '') // Remove breadcrumbs
      .trim();
  }

  private getBestVoice(settings: SpeechSettings): SpeechSynthesisVoice | null {
    if (settings.voiceURI) {
      const selected = this.voices.find(v => v.voiceURI === settings.voiceURI);
      if (selected) return selected;
    }

    // Fallback logic
    const indiaVoice = this.voices.find(v => v.lang.includes('en-IN') && !v.name.includes('Premium'));
    if (indiaVoice) return indiaVoice;

    const ukVoice = this.voices.find(v => v.lang.includes('en-GB'));
    if (ukVoice) return ukVoice;

    const usVoice = this.voices.find(v => v.lang.includes('en-US'));
    if (usVoice) return usVoice;

    return this.voices.length > 0 ? this.voices[0] : null;
  }

  public speak(
    text: string, 
    settings: SpeechSettings, 
    onStart: () => void, 
    onEnd: () => void, 
    onError: () => void
  ) {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      console.error("Voice playback is not supported by this browser.");
      onEnd();
      return;
    }

    if (this.voices.length === 0) {
      this.loadVoices();
    }

    // Very important: Cancel ONLY BEFORE creating a new utterance
    this.cancel();

    const cleanText = this.stripMarkdown(text);
    if (!cleanText) {
      onEnd();
      return;
    }

    const sentences = cleanText.match(/[^.!?]+[.!?]*/g) || [cleanText];
    let currentIndex = 0;
    let isFinished = false;
    let timeoutId: NodeJS.Timeout | null = null;
    let hasStarted = false;

    const cleanup = () => {
      isFinished = true;
      if (timeoutId) {
        clearTimeout(timeoutId);
        timeoutId = null;
      }
    };

    const speakNextSentence = (retryCount = 0) => {
      if (isFinished) return;

      if (currentIndex >= sentences.length) {
        console.log("Speech Finished");
        cleanup();
        onEnd();
        return;
      }

      const sentence = sentences[currentIndex].trim();
      if (!sentence) {
        currentIndex++;
        speakNextSentence(0);
        return;
      }

      const utterance = new SpeechSynthesisUtterance(sentence);
      
      const selectedVoice = this.getBestVoice(settings);
      if (selectedVoice) {
        utterance.voice = selectedVoice;
        utterance.lang = selectedVoice.lang;
        if (currentIndex === 0 && retryCount === 0) {
          console.log(`Selected Voice: ${selectedVoice.name} (${selectedVoice.lang})`);
        }
      } else {
        utterance.lang = settings.language || 'en-IN';
      }

      utterance.pitch = settings.pitch || 1.0;
      utterance.rate = settings.rate || 1.0;
      utterance.volume = settings.volume || 1.0;

      utterance.onstart = () => {
        if (timeoutId) {
          clearTimeout(timeoutId);
          timeoutId = null;
        }
        if (!hasStarted) {
          hasStarted = true;
          console.log("Speech Started");
          onStart();
        }
      };

      utterance.onboundary = (event) => {
        // Optional highlighting logic could be placed here
      };

      utterance.onend = () => {
        if (timeoutId) {
          clearTimeout(timeoutId);
          timeoutId = null;
        }
        currentIndex++;
        speakNextSentence(0);
      };

      utterance.onerror = (e) => {
        if (e.error === 'interrupted' || e.error === 'canceled') {
          console.log(`Speech ${e.error}`);
          cleanup();
          onEnd();
          return;
        }
        console.error('Speech Error:', e.error || 'unknown error', e);
        
        if (retryCount === 0) {
          console.log("Voice Retry triggered from error.");
          this.cancel();
          setTimeout(() => speakNextSentence(1), 250);
        } else {
          cleanup();
          onError();
        }
      };

      // 3-second timeout protection
      timeoutId = setTimeout(() => {
        console.warn("Speech start timed out.");
        if (!hasStarted && !isFinished) {
          console.log("Voice Retry triggered.");
          this.cancel();
          if (retryCount === 0) {
            speakNextSentence(1); // Retry once
          } else {
            console.error("Speech Synthesis failed after retry. Resetting.");
            cleanup();
            onError();
          }
        }
      }, 3000);

      window.speechSynthesis.speak(utterance);
    };

    speakNextSentence(0);
  }

  public cancel() {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }

  public isSpeaking(): boolean {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      return window.speechSynthesis.speaking;
    }
    return false;
  }

  public getAvailableVoices() {
    return this.voices;
  }
}

export const voiceOutputService = VoiceOutputService.getInstance();
