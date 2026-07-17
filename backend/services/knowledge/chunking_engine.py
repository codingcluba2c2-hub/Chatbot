import re
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime

class BlockNode:
    def __init__(self, block_type: str, title: str, content: str, page: int):
        self.block_type = block_type
        self.title = title
        self.content = content
        self.page = page

class SubsectionNode:
    def __init__(self, title: str):
        self.title = title
        self.blocks: List[BlockNode] = []

class SectionNode:
    def __init__(self, title: str):
        self.title = title
        self.subsections: List[SubsectionNode] = []

class DocumentTree:
    def __init__(self):
        self.sections: List[SectionNode] = []

class DocumentASTBuilder:
    def __init__(self, raw_text: str):
        self.raw_text = raw_text
        self.page_map = []
        self.clean_text = ""
        self._build_page_map()
        self.lines = [line.strip() for line in self.clean_text.split('\n') if line.strip()]
        self.ast = DocumentTree()
        self._build_ast()

    def _build_page_map(self):
        clean_text = ""
        last_idx = 0
        for match in re.finditer(r'\n*__PAGE_BOUNDARY_(\d+)__\n*', self.raw_text):
            chunk_part = self.raw_text[last_idx:match.start()]
            clean_text += chunk_part
            self.page_map.append((len(clean_text), int(match.group(1))))
            last_idx = match.end()
        clean_text += self.raw_text[last_idx:]
        self.clean_text = clean_text

    def get_page_for_idx(self, text_idx: int) -> int:
        page_num = 1
        for p_idx, p_num in self.page_map:
            if text_idx >= p_idx:
                page_num = p_num
            else:
                break
        return page_num

    def _is_section(self, line: str) -> bool:
        return bool(re.match(r'^(?:#\s+|\d+\.\s+)(.*)', line)) and not bool(re.match(r'^(?:##\s+|\d+\.\d+\.\s+)(.*)', line))
        
    def _is_subsection(self, line: str) -> bool:
        return bool(re.match(r'^(?:##\s+|\d+\.\d+\.\s+)(.*)', line))

    def _is_title(self, line: str) -> bool:
        if self._is_section(line) or self._is_subsection(line):
            return False
        # Titles are short and don't end in typical sentence punctuation.
        if len(line.split()) <= 6 and not line.endswith(('.', '?', '!', ':', ';', ',')):
            return True
        return False

    def _is_list(self, line: str) -> bool:
        return bool(re.match(r'^[\*\-•]\s', line))
        
    def _is_table(self, line: str) -> bool:
        return line.startswith('|')
        
    def _is_faq(self, line: str) -> bool:
        return line.lower().startswith('q:') or line.lower().startswith('question:')

    def _detect_type(self, content: str, title: str = "") -> str:
        c_lower = content.lower()
        t_lower = title.lower()
        
        # Determine if it's a KeyValueTable
        # Must have at least some "key: value" or bullet "key: value" lines
        if re.search(r'[\*\-•]?\s*.+?:\s*.+', content) and not self._is_faq(content):
            if any(kw in t_lower for kw in ['details', 'profile', 'identity', 'contact', 'categorization', 'status']):
                return "KeyValueTable"
                
        if bool(re.match(r'^[\*\-•]\s', content)): return "Bullet List"
        if c_lower.startswith('q:') or c_lower.startswith('question:'): return "FAQ"
        
        for kw in ['overview', 'key points', 'company identity details', 'technology details', 'leadership details', 'policy details', 'service details', 'location details', 'glossary', 'contact details', 'related keywords', 'related queries', 'timeline', 'mission']:
            if kw in t_lower:
                if kw == 'overview': return 'Overview'
                if kw == 'key points': return 'Bullet List'
                if kw == 'company identity details': return 'KeyValueTable'
                if kw == 'faq': return 'FAQ'
                if kw == 'timeline': return 'Timeline'
                if kw == 'mission': return 'Overview'
                if kw == 'glossary': return 'Glossary'
                return kw.title()
                
        return "Paragraph"

    def _build_ast(self):
        active_section = SectionNode("General")
        active_subsection = SubsectionNode("General")
        active_section.subsections.append(active_subsection)
        self.ast.sections.append(active_section)
        
        current_title = "Overview"
        
        char_idx_tracker = 0
        i = 0
        
        while i < len(self.lines):
            line = self.lines[i]
            page_num = self.get_page_for_idx(char_idx_tracker)
            
            if not line or line.startswith('__PAGE_BOUNDARY') or line.startswith('|') or line.startswith('---'):
                char_idx_tracker += len(line) + 1
                i += 1
                continue
                
            if self._is_section(line):
                active_section = SectionNode(line)
                active_subsection = SubsectionNode("General") # NEVER inherit section title
                active_section.subsections.append(active_subsection)
                self.ast.sections.append(active_section)
                current_title = "Overview"
                char_idx_tracker += len(line) + 1
                i += 1
                continue
                
            if self._is_subsection(line):
                active_subsection = SubsectionNode(line)
                active_section.subsections.append(active_subsection)
                current_title = "Overview"
                char_idx_tracker += len(line) + 1
                i += 1
                continue
                
            if self._is_title(line):
                current_title = line
                char_idx_tracker += len(line) + 1
                i += 1
                continue
                
            content_accumulation = []
            
            if self._is_list(line):
                # Accumulate lists AND their wrapped lines
                while i < len(self.lines):
                    l = self.lines[i]
                    if l.startswith('|') or l.startswith('---'):
                        i += 1
                        char_idx_tracker += len(l) + 1
                        continue
                    if self._is_section(l) or self._is_subsection(l) or self._is_title(l):
                        break
                    # If it's a new content block that is NOT a bullet, stop.
                    # But allow wrapped lines (lines that don't look like new structure)
                    if not self._is_list(l) and (self._is_faq(l)):
                        break
                    
                    content_accumulation.append(l)
                    char_idx_tracker += len(l) + 1
                    i += 1
            elif self._is_faq(line):
                # Accumulate FAQ AND its wrapped lines
                while i < len(self.lines):
                    l = self.lines[i]
                    if l.startswith('|') or l.startswith('---'):
                        i += 1
                        char_idx_tracker += len(l) + 1
                        continue
                    if self._is_section(l) or self._is_subsection(l) or self._is_title(l) or self._is_list(l):
                        break
                    content_accumulation.append(l)
                    char_idx_tracker += len(l) + 1
                    i += 1
            else:
                # Accumulate paragraph AND its wrapped lines
                while i < len(self.lines):
                    l = self.lines[i]
                    if l.startswith('|') or l.startswith('---'):
                        i += 1
                        char_idx_tracker += len(l) + 1
                        continue
                    if self._is_section(l) or self._is_subsection(l) or self._is_title(l) or self._is_list(l) or self._is_faq(l):
                        break
                    content_accumulation.append(l)
                    char_idx_tracker += len(l) + 1
                    i += 1
                    
            if not content_accumulation:
                continue
                
            # Stitching logic
            if self._is_list(content_accumulation[0]) or self._is_faq(content_accumulation[0]):
                # For lists, if a line doesn't start with a bullet, it's a wrapped line of the previous bullet
                stitched_lines = []
                for l in content_accumulation:
                    if self._is_list(l) or self._is_faq(l) or not stitched_lines:
                        stitched_lines.append(l)
                    else:
                        stitched_lines[-1] += " " + l
                content_str = "\n".join(stitched_lines)
            else:
                # Normal paragraph: space-stitch all wrapped lines
                content_str = " ".join(content_accumulation)
            
            block_type = self._detect_type(content_str, current_title)
            
            leaf = BlockNode(
                block_type=block_type,
                title=current_title,
                content=content_str,
                page=page_num
            )
            active_subsection.blocks.append(leaf)
            current_title = "Overview"

class SemanticValidator:
    @staticmethod
    def validate(ast: DocumentTree) -> bool:
        for sec in ast.sections:
            if not sec.subsections:
                return False
            for subsec in sec.subsections:
                if subsec.title == sec.title and subsec.title != "General":
                    return False
                for block in subsec.blocks:
                    if not block.content.strip():
                        return False
                    if "about:blank" in block.content.lower():
                        return False
                    if '|' in block.content:
                        return False
        return True

class MetadataExtractor:
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        words = re.findall(r'\b[A-Za-z]{4,}\b', text)
        import collections
        return [k.title() for k, _ in collections.Counter(w.lower() for w in words).most_common(3)]

class SemanticChunkGenerator:
    def __init__(self, document_id: str):
        self.document_id = document_id
        self.seen_hashes = set()
        
    def generate(self, ast: DocumentTree) -> List[Dict[str, Any]]:
        chunks = []
        global_chunk_idx = 1
        
        for section_idx, section in enumerate(ast.sections):
            for subsection_idx, subsection in enumerate(section.subsections):
                for block_idx, leaf in enumerate(subsection.blocks):
                        
                    keywords = MetadataExtractor.extract_keywords(leaf.content)
                    word_count = len(leaf.content.split())
                    
                    ui_content = f"Section\n{section.title}\n\nSubsection\n{subsection.title}\n\nBlock Type\n{leaf.block_type}\n\nTitle\n{leaf.title}\n\nContent\n{leaf.content}"
                    
                    chunk_hash = hashlib.sha256(leaf.content.encode('utf-8')).hexdigest()
                    
                    if chunk_hash in self.seen_hashes:
                        continue
                    self.seen_hashes.add(chunk_hash)
                    
                    chunk_data = {
                        "content": ui_content,
                        "metadata": {
                            "chunk_id": f"chk_{global_chunk_idx}",
                            "chunk_number": global_chunk_idx,
                            "display_order": global_chunk_idx,
                            "page": leaf.page,
                            "section": section.title,
                            "subsection": subsection.title,
                            "block_type": leaf.block_type,
                            "title": leaf.title,
                            "content_only": leaf.content,
                            "keywords": keywords,
                            "word_count": word_count,
                            "token_count": int(word_count * 1.3),
                            "char_count": len(leaf.content),
                            "hash": chunk_hash,
                            "section_id": f"sec_{section_idx}",
                            "subsection_id": f"subsec_{subsection_idx}",
                            "block_id": f"blk_{block_idx}",
                            "created_at": datetime.utcnow().isoformat()
                        }
                    }
                    
                    chunks.append(chunk_data)
                    global_chunk_idx += 1
                    
        return chunks

class ChunkingEngine:
    @staticmethod
    def chunk_text(raw_text: str, document_id: str = "unknown", source: str = "unknown", document_type: str = "document") -> List[Dict[str, Any]]:
        tree_builder = DocumentASTBuilder(raw_text)
        if not SemanticValidator.validate(tree_builder.ast):
            print("WARNING: AST Validation Failed.")
            
        generator = SemanticChunkGenerator(document_id)
        return generator.generate(tree_builder.ast)
