# 03. Frontend UI & Detailed RAG Flow

This document details the NextJS frontend architecture, the UI components, and the step-by-step execution flow of the Retrieval-Augmented Generation (RAG) process.

---

## 1. Frontend Architecture

The frontend is built on **NextJS** using the modern App Router (`src/app/`). It is styled heavily with **TailwindCSS** for a responsive, enterprise-grade look and feel.

### Component Hierarchy

```text
frontend/src/
├── app/
│   ├── page.tsx (The main Chat UI page)
│   ├── layout.tsx (Global layout, fonts)
│   └── admin/
│       ├── page.tsx (Admin Dashboard)
│       └── knowledge/ (Knowledge Base Management)
│
├── components/
│   ├── chat/
│   │   ├── ChatMessage.tsx (Renders individual chat bubbles)
│   │   ├── InputArea.tsx (Text area for user input)
│   │   └── DeveloperSidebar.tsx (Displays the Execution Graph)
│   │
│   └── admin/
│       └── knowledge/
│           ├── KnowledgeBaseModule.tsx (Main Document Table)
│           └── EmbeddingsTab.tsx (The Vector Debugging Dashboard)
```

### State Management & Local Storage
Instead of a complex Redux store or backend authentication database, the application relies on **React State** for UI interactivity and **Browser LocalStorage** for persistence.
- When a user opens the chat, a unique `session_id` is generated and saved to LocalStorage.
- User preferences (like Assistant Name) are kept in LocalStorage and passed in the `metadata` object of every API request.
- This creates a seamless, stateless backend that still behaves as if it has a memory.

---

## 2. RAG Execution Flow in Detail

RAG (Retrieval-Augmented Generation) is the process of fetching private data and giving it to an LLM to generate an answer. Here is exactly what happens when a user asks a complex question.

### The Scenario
**User types:** *"How many earned leaves do I get?"*

### Step-by-Step Flow

1. **UI Submission**: The user clicks send in `InputArea.tsx`. The message is appended to the local chat state as a user bubble.
2. **API Call**: A `POST` request is fired to `/api/chat`.
3. **Pipeline Begins**:
   - `NormalizeStep`: Trims whitespace and fixes typos.
   - `ConversationIntelligence`: Checks if the user is trying to change their name. (Result: Skip)
   - `Greeting/FAQ/FastPath`: Checks if this is a known static question. (Result: Skip, because this requires reading a document).
4. **KnowledgeSearchStep (The Retrieval)**:
   - The query *"How many earned leaves do I get?"* is sent to the `SentenceTransformer` model.
   - The model generates a 384-dimensional vector (an array of numbers).
   - This query vector is sent to the **Qdrant Vector Database**.
   - Qdrant compares the query vector against all document chunks using **Cosine Similarity**.
   - Qdrant returns the Top 3 chunks (e.g., Chunk 4, Chunk 6) that have a similarity score above the threshold (e.g., `0.75`).
5. **LLMStep (The Generation)**:
   - The backend constructs a prompt: *"Answer the question using the following context. Context: [Text from Chunk 4 and Chunk 6]"*.
   - This prompt is sent to the Google Gemini API.
   - Gemini reads the chunks, extracts the exact number of days, and generates a polite, conversational response.
6. **UI Render**: The JSON response hits the frontend, and `ChatMessage.tsx` renders the bot's answer.

---

## 3. Developer Mode & Execution Graph

When **Developer Mode** is toggled ON in the UI, a sidebar appears. This is a massive feature for AI debugging.

- **Trace Object**: The backend attaches a `trace` dictionary to every response. This contains the exact start time, end time, and duration of every single pipeline step.
- **Execution Graph**: The sidebar renders a flowchart of nodes.
  - **Node Color**: Green means success, Red means error, Gray means skipped.
  - **Decision Status**: If a node says `Continue`, it means the step finished its job and passed control to the next step. If it says `Stop`, it means the step intercepted the query and halted the pipeline (saving time).
  - **Total Backend Time**: Displayed at the bottom, proving to the user how fast the local pipeline runs compared to the LLM generation step.

---

## 4. The Embeddings Debugging Dashboard

Inside the Admin Knowledge Base, the **Embeddings Tab** is a critical tool for AI Engineers to understand *how* the text is being processed.

### Terminology Explained (Simple English)

- **Dimension (384)**: When the AI reads a chunk of text, it converts it into a list of exactly 384 numbers. Think of it like 384 different "sliders" or "traits" that describe the meaning of that text.
- **Cosine Distance**: The mathematical formula used to calculate how similar two vectors are. If the vectors point in the exact same direction, the cosine similarity is 1.0 (perfect match). If they are completely unrelated, it drops toward 0.
- **Min/Max/Mean**: The smallest, largest, and average float values across the 384 numbers. Useful to ensure the embedding model isn't outputting garbage data (like all zeros).
- **L2 Norm**: The total "length" or "magnitude" of the vector. Standardized models usually output vectors with an L2 Norm close to 1.0.

### Features
- **Similarity Playground**: Allows the admin to type a query and immediately see how Qdrant scores it against the chunks.
- **Vector Distribution (Histogram)**: Visualizes the spread of the 384 numbers using a Recharts BarChart. It bins the values (e.g., how many numbers are between -0.1 and 0.1) to show the semantic "shape" of the chunk.
- **Top 20 Magnitude**: Automatically highlights the most extreme values in the vector. These values often represent the most defining "traits" of that specific text chunk.

---

## 5. Retrieval Test & Thresholds

Also in the Admin panel is the **Retrieval Test** tab.

- **Similarity Score**: A number between 0.0 and 1.0. A score of `0.85` means the AI is highly confident that the chunk is related to the query. A score of `0.40` means it's probably unrelated.
- **Why a Threshold of 0.75?**: If we pass completely irrelevant chunks to the LLM, the LLM will hallucinate or give wrong answers. By setting a strict cut-off (e.g., only accept chunks with a score > 0.75), we guarantee that the LLM only receives highly relevant context.
- **Top K**: The maximum number of chunks we return. If `Top K = 3`, we only give the top 3 best matching chunks to the LLM. This saves LLM token costs and prevents the context window from overflowing.

---

## Interview Questions & Best Answers

**Q: Explain the flow of RAG in this application as if I were a beginner.**
> **A:** "Imagine you have a massive textbook (your documents). You chop the textbook into paragraphs (Chunks) and use a special algorithm to assign a unique barcode (Embedding) to each paragraph based on its meaning. You store these in a smart filing cabinet (Vector Database). When a user asks a question, the system turns their question into a barcode, asks the filing cabinet to find the 3 paragraphs with the most similar barcodes, and then hands those 3 paragraphs to a smart reader (the LLM) to write a summary for the user."

**Q: How does the frontend maintain state without a database?**
> **A:** "It leverages the browser's `LocalStorage`. When a user visits, we generate a unique UUID for their session. We store their preferences, like how they want the bot to address them, in LocalStorage. Every time the frontend calls the backend API, it attaches this LocalStorage data in the request payload. The backend reads it, acts on it, and sends it back. It's a completely stateless backend design that perfectly simulates a stateful conversation."

**Q: Why did you build the Embeddings Visualizer tab?**
> **A:** "AI can sometimes feel like a 'black box'—data goes in, answers come out, and if something breaks, you don't know why. The Embeddings tab exposes the raw mathematics behind the AI. By seeing the actual 384 numbers, visualizing their distribution, and testing similarity scores live, engineers can instantly debug why a certain document isn't being retrieved correctly by the RAG pipeline."
