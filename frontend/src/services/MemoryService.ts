// frontend/src/services/MemoryService.ts

export interface SessionMemory {
  user_name: string | null;
  preferred_name: string | null;
  company: string | null;
  designation: string | null;
  city: string | null;
  facts: Record<string, any>;
  updated_at: string;
}

const STORAGE_KEY = "chatbot_session_memory";

const DEFAULT_MEMORY: SessionMemory = {
  user_name: null,
  preferred_name: null,
  company: null,
  designation: null,
  city: null,
  facts: {},
  updated_at: new Date().toISOString()
};

export class MemoryService {
  static loadMemory(): SessionMemory {
    if (typeof window === "undefined") return DEFAULT_MEMORY;
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored) as SessionMemory;
      }
    } catch (e) {
      console.warn("Failed to read SessionMemory from localStorage", e);
    }
    return DEFAULT_MEMORY;
  }

  static saveMemory(memory: SessionMemory): void {
    if (typeof window === "undefined") return;
    try {
      memory.updated_at = new Date().toISOString();
      localStorage.setItem(STORAGE_KEY, JSON.stringify(memory));
    } catch (e) {
      console.warn("Failed to save SessionMemory to localStorage", e);
    }
  }

  static updateMemory(updates: Partial<SessionMemory>): SessionMemory {
    const currentMemory = this.loadMemory();
    const newMemory = { ...currentMemory, ...updates };
    this.saveMemory(newMemory);
    return newMemory;
  }

  static clearMemory(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem(STORAGE_KEY);
  }
}
