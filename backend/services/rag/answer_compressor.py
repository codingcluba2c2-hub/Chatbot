import re
import nltk
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
import networkx as nx

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

class AnswerCompressor:
    @staticmethod
    def clean_text(raw_text: str) -> str:
        text = re.sub(r'__PAGE_BOUNDARY_\d+__', '', raw_text)
        text = re.sub(r'(?i)Confidential - Internal Knowledge Base', '', text)
        text = re.sub(r'(?i)Mobiloitte Technologies - Enterprise AI & Digital Engineering \d+', '', text)
        # We don't remove newlines completely to preserve list items, but we collapse multiple spaces
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        return text.strip()

    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        # First split by explicit newlines, then by NLTK sent_tokenize
        lines = text.split('\n')
        sentences = []
        for line in lines:
            if len(line.strip()) < 3:
                continue
            sents = nltk.tokenize.sent_tokenize(line)
            for s in sents:
                # Merge small orphaned words with previous if possible
                if len(s.split()) < 3 and sentences:
                    sentences[-1] = sentences[-1] + " " + s
                else:
                    sentences.append(s)
        return [s.strip() for s in sentences if len(s.strip()) > 3]

    @staticmethod
    def score_sentences(query: str, sentences: List[str]) -> List[Tuple[float, str]]:
        if not sentences:
            return []
            
        corpus = [query] + sentences
        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(corpus)
        except ValueError:
            return [(1.0, s) for s in sentences]

        query_vector = tfidf_matrix[0:1]
        sentence_vectors = tfidf_matrix[1:]
        
        similarities = (sentence_vectors * query_vector.T).toarray().flatten()
        
        sentence_sim_matrix = (sentence_vectors * sentence_vectors.T).toarray()
        nx_graph = nx.from_numpy_array(sentence_sim_matrix)
        
        try:
            scores = nx.pagerank(nx_graph, max_iter=100)
        except:
            scores = {i: 1.0 for i in range(len(sentences))}
            
        final_scores = []
        for i, sentence in enumerate(sentences):
            # Weigh query similarity heavily
            combined_score = (similarities[i] * 0.85) + (scores[i] * 0.15)
            # Bonus for exact keyword matches
            keywords = set(query.lower().replace("/", " ").replace("-", " ").split())
            bonus = 0.0
            for kw in keywords:
                if len(kw) > 3 and kw in sentence.lower():
                    bonus += 0.2
            
            final_scores.append((combined_score + bonus, sentence))
            
        final_scores.sort(key=lambda x: x[0], reverse=True)
        return final_scores

    @staticmethod
    def compress(query: str, chunks: List[Dict[str, Any]], max_sentences: int = 5) -> Dict[str, Any]:
        raw_text = " ".join([chunk.get("text", "") for chunk in chunks])
        original_length = len(raw_text)
        
        clean = AnswerCompressor.clean_text(raw_text)
        sentences = AnswerCompressor.split_into_sentences(clean)
        scored = AnswerCompressor.score_sentences(query, sentences)
        
        # Filter high relevance sentences
        filtered = []
        seen = set()
        for score, sent in scored:
            if score > 0.05 and sent.lower() not in seen:
                seen.add(sent.lower())
                filtered.append(sent)
                
        # If nothing passed the threshold but we have sentences, just take the top 1
        if not filtered and scored:
            filtered.append(scored[0][1])
            
        final_sentences = filtered[:max_sentences]
        compressed_text = "\n".join(final_sentences)
        
        return {
            "compressed_text": compressed_text,
            "sentences": final_sentences,
            "metrics": {
                "original_length": original_length,
                "compressed_length": len(compressed_text),
                "total_sentences": len(sentences),
                "kept_sentences": len(final_sentences)
            }
        }
