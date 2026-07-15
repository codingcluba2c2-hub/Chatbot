import time
import re
from typing import List, Dict, Any, Tuple
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
import networkx as nx

# Ensure NLTK tokenizers are available
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

class TextCleaner:
    @staticmethod
    def clean(text: str) -> str:
        # Remove pagination markers
        text = re.sub(r'__PAGE_BOUNDARY_\d+__', '', text)
        # Remove confidential headers/footers
        text = re.sub(r'(?i)Confidential - Internal Knowledge Base', '', text)
        text = re.sub(r'(?i)Mobiloitte Technologies - Enterprise AI & Digital Engineering \d+', '', text)
        # Remove broken hyphenation
        text = re.sub(r'([a-zA-Z]+)-\s*\n\s*([a-zA-Z]+)', r'\1\2', text)
        # Collapse multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

class QuestionAnalyzer:
    @staticmethod
    def detect_type(query: str) -> str:
        query_lower = query.lower()
        words = query_lower.split()
        
        # Long explanatory queries
        if any(w in query_lower for w in ["explain", "describe", "detail", "how does", "what is the process", "elaborate"]):
            return "long"
            
        # Short factual queries
        if len(words) <= 5 or any(w in query_lower for w in ["how many", "who", "when", "where", "what is the name", "count"]):
            return "short"
            
        return "medium"

class TopicExtractor:
    @staticmethod
    def extract(query: str) -> List[str]:
        # Remove common conversational prefixes
        clean_query = query.lower()
        prefixes = [
            "tell me about", "what are the details of", "what is", "what are",
            "explain to me", "can you provide", "i want to know about", "give me details on"
        ]
        for prefix in prefixes:
            if clean_query.startswith(prefix):
                clean_query = clean_query[len(prefix):].strip()
        
        # Split by comma, "and", "or"
        # e.g., "sick leave, services, and managers details" -> ["sick leave", "services", "managers details"]
        parts = re.split(r',|\band\b|\bor\b', clean_query)
        topics = [p.strip() for p in parts if p.strip() and len(p.strip().split()) > 0]
        
        # If no valid topics extracted, fallback to the original query
        if not topics:
            return [query]
            
        return topics

class SentenceRanker:
    @staticmethod
    def rank(query: str, sentences: List[str]) -> List[Tuple[float, str]]:
        if not sentences:
            return []
            
        # Combine query with sentences for TF-IDF to get similarities to query
        corpus = [query] + sentences
        
        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(corpus)
        except ValueError:
            # Fallback if corpus is completely empty of valid words
            return [(1.0, s) for s in sentences]

        # Calculate similarity between query and all sentences
        query_vector = tfidf_matrix[0:1]
        sentence_vectors = tfidf_matrix[1:]
        
        # Calculate cosine similarity of each sentence to the query
        similarities = (sentence_vectors * query_vector.T).toarray().flatten()
        
        # Build TextRank graph for sentence-to-sentence similarity
        # Similarity matrix between sentences
        sentence_sim_matrix = (sentence_vectors * sentence_vectors.T).toarray()
        
        # NetworkX PageRank
        nx_graph = nx.from_numpy_array(sentence_sim_matrix)
        try:
            scores = nx.pagerank(nx_graph, max_iter=100)
        except:
            # Fallback if pagerank fails to converge
            scores = {i: 1.0 for i in range(len(sentences))}
            
        # Combine Query Similarity + TextRank Score
        final_scores = []
        for i, sentence in enumerate(sentences):
            # Weigh query similarity heavily, but boost by centrality (TextRank)
            combined_score = (similarities[i] * 0.7) + (scores[i] * 0.3)
            final_scores.append((combined_score, sentence))
            
        # Sort by highest score
        final_scores.sort(key=lambda x: x[0], reverse=True)
        return final_scores

class ResponseFormatter:
    @staticmethod
    def format_single(ranked_sentences: List[Tuple[float, str]], q_type: str) -> str:
        if not ranked_sentences:
            return "I couldn't find a direct answer in the knowledge base."
            
        seen = set()
        selected = []
        for score, sentence in ranked_sentences:
            if sentence.lower() not in seen and len(sentence.split()) > 3:
                seen.add(sentence.lower())
                selected.append(sentence)
                
        if q_type == "short":
            return " ".join(selected[:2])
        elif q_type == "medium":
            return " ".join(selected[:4])
        else: # long
            final_sentences = selected[:6]
            if len(final_sentences) == 1:
                return final_sentences[0]
            response = "Here are the key details:\n\n"
            for s in final_sentences:
                response += f"• {s}\n"
            return response.strip()

    @staticmethod
    def format_multi(topic_results: List[Dict[str, Any]]) -> str:
        if not topic_results:
            return "I couldn't find details matching your request."
            
        response_parts = []
        response_parts.append("Here is the requested information broken down by topic:\n")
        
        for result in topic_results:
            topic_title = result["topic"].title()
            sentences = result["sentences"]
            if not sentences:
                continue
                
            # Take top 2 sentences per topic to keep it concise and good-looking
            content = " ".join([s for score, s in sentences[:2]])
            response_parts.append(f"**{topic_title}**\n{content}\n")
            
        return "\n".join(response_parts).strip()

class LocalResponseGenerator:
    @staticmethod
    def generate(query: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        t0 = time.time()
        
        # 1. Extract and Clean Text
        raw_text = " ".join([chunk.get("text", "") for chunk in chunks])
        clean_text = TextCleaner.clean(raw_text)
        
        # 2. Tokenize Sentences
        sentences = nltk.tokenize.sent_tokenize(clean_text)
        
        # 3. Analyze Topics
        topics = TopicExtractor.extract(query)
        q_type = QuestionAnalyzer.detect_type(query)
        
        total_sentences_selected = 0
        keywords = []
        
        # 4. Generate Response
        if len(topics) > 1:
            # Multi-topic processing
            topic_results = []
            seen_sentences = set()
            
            for topic in topics:
                ranked = SentenceRanker.rank(topic, sentences)
                
                # Score all sentences for this topic, but only keep the top 2 that haven't been used
                unique_ranked = []
                for score, sentence in ranked:
                    if sentence.lower() not in seen_sentences and len(sentence.split()) > 3:
                        unique_ranked.append((score, sentence))
                        if len(unique_ranked) >= 2:
                            break
                            
                for score, sentence in unique_ranked:
                    seen_sentences.add(sentence.lower())
                
                topic_results.append({
                    "topic": topic,
                    "sentences": unique_ranked
                })
                
                # Track metadata
                if unique_ranked:
                    top_sentence = unique_ranked[0][1].lower()
                    query_words = set(re.findall(r'\b\w+\b', topic.lower()))
                    for w in query_words:
                        if len(w) > 3 and w in top_sentence:
                            keywords.append(w)
                
                total_sentences_selected += min(len(unique_ranked), 2)
                
            formatted_response = ResponseFormatter.format_multi(topic_results)
            
        else:
            # Single topic processing
            ranked = SentenceRanker.rank(query, sentences)
            formatted_response = ResponseFormatter.format_single(ranked, q_type)
            
            # Track metadata
            if ranked:
                top_sentence = ranked[0][1].lower()
                query_words = set(re.findall(r'\b\w+\b', query.lower()))
                for w in query_words:
                    if len(w) > 3 and w in top_sentence:
                        keywords.append(w)
                        
            total_sentences_selected = min(len(ranked), 2 if q_type=="short" else 4 if q_type=="medium" else 6)
        
        t1 = time.time()
        processing_time_ms = int((t1 - t0) * 1000)
        
        return {
            "response": formatted_response,
            "metadata": {
                "Response Source": "Local Generator (Multi-Topic)",
                "Fallback Used": True,
                "Question Type": "Multi-Topic" if len(topics) > 1 else q_type.capitalize(),
                "Topics Detected": len(topics),
                "Sentences Selected": total_sentences_selected,
                "Keywords Matched": list(set(keywords)) if keywords else ["None"],
                "Processing Time": f"{processing_time_ms} ms"
            }
        }
