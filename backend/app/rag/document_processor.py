import os
import re
from typing import List, Dict, Any
from pypdf import PdfReader
from docx import Document as DocxDocument

class DocumentProcessor:
    @staticmethod
    def extract_text_from_file(file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text from file.
        Returns a list of dicts: [{"page": int, "text": str}]
        """
        ext = os.path.splitext(file_path)[1].lower()
        pages_data = []

        if ext == ".pdf":
            try:
                reader = PdfReader(file_path)
                for idx, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    clean_text = DocumentProcessor.clean_text(text)
                    if clean_text:
                        pages_data.append({"page": idx + 1, "text": clean_text})
            except Exception as e:
                raise ValueError(f"Error reading PDF file: {str(e)}")

        elif ext == ".docx":
            try:
                doc = DocxDocument(file_path)
                full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                clean_text = DocumentProcessor.clean_text(full_text)
                if clean_text:
                    pages_data.append({"page": 1, "text": clean_text})
            except Exception as e:
                raise ValueError(f"Error reading DOCX file: {str(e)}")

        elif ext in [".txt", ".md"]:
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                
                # Check for explicit Page markers like (Page 1) or SECTION
                sections = re.split(r'\(Page\s*(\d+)\)', content, flags=re.IGNORECASE)
                if len(sections) > 1:
                    # Alternates: preamble, page_num, section_text, page_num, section_text...
                    # First part is preamble or page 1
                    first_text = DocumentProcessor.clean_text(sections[0])
                    if first_text:
                        pages_data.append({"page": 1, "text": first_text})
                    for i in range(1, len(sections), 2):
                        page_num = int(sections[i])
                        sec_text = DocumentProcessor.clean_text(sections[i+1]) if i+1 < len(sections) else ""
                        if sec_text:
                            pages_data.append({"page": page_num, "text": sec_text})
                else:
                    clean_text = DocumentProcessor.clean_text(content)
                    if clean_text:
                        pages_data.append({"page": 1, "text": clean_text})
            except Exception as e:
                raise ValueError(f"Error reading text file: {str(e)}")
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        return pages_data

    @staticmethod
    def clean_text(text: str) -> str:
        # Normalize whitespace, remove weird non-printable characters
        text = re.sub(r'[\r\f\v]', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @staticmethod
    def chunk_document(
        pages_data: List[Dict[str, Any]], 
        document_id: str, 
        document_name: str,
        chunk_size: int = 800,
        chunk_overlap: int = 150
    ) -> List[Dict[str, Any]]:
        """
        Splits pages into overlapping chunks while retaining page metadata.
        """
        chunks = []
        chunk_counter = 0

        for page_info in pages_data:
            page_num = page_info["page"]
            text = page_info["text"]
            
            # Split by paragraphs or sentences first
            paragraphs = text.split("\n\n")
            current_chunk = ""
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                if len(current_chunk) + len(para) <= chunk_size:
                    current_chunk += ("\n\n" if current_chunk else "") + para
                else:
                    if current_chunk:
                        chunk_counter += 1
                        chunks.append({
                            "chunk_id": f"{document_id}_c{chunk_counter}",
                            "document_id": document_id,
                            "document_name": document_name,
                            "page": page_num,
                            "text": current_chunk.strip()
                        })
                    
                    # If paragraph itself is larger than chunk_size, split by sentences or slice
                    if len(para) > chunk_size:
                        sub_start = 0
                        while sub_start < len(para):
                            sub_end = min(sub_start + chunk_size, len(para))
                            sub_text = para[sub_start:sub_end]
                            chunk_counter += 1
                            chunks.append({
                                "chunk_id": f"{document_id}_c{chunk_counter}",
                                "document_id": document_id,
                                "document_name": document_name,
                                "page": page_num,
                                "text": sub_text.strip()
                            })
                            if sub_end == len(para):
                                break
                            sub_start += (chunk_size - chunk_overlap)
                        current_chunk = ""
                    else:
                        current_chunk = para

            if current_chunk:
                chunk_counter += 1
                chunks.append({
                    "chunk_id": f"{document_id}_c{chunk_counter}",
                    "document_id": document_id,
                    "document_name": document_name,
                    "page": page_num,
                    "text": current_chunk.strip()
                })

        return chunks
