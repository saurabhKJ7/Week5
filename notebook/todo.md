Integrate Unstructured & Docling pipelines to replace current DocumentProcessor; support cleaned text extraction + metadata
Add support for additional formats (HTML, XLSX, PPTX, images, tables, charts) in document pipeline
Add multimodal vision model integration (GPT-4V / Claude-Vision) for image understanding inside documents
Implement intelligent document hierarchy preservation (sections, headings) during parsing
Replace Chroma usage with hybrid search setup: Chroma (vector) + keyword BM25, enable metadata filters
Implement query decomposition agent that plans sub-queries before final answer
Add smart summarisation endpoint to generate executive summaries across multiple docs
Implement relationship mapping engine (graph extraction) and endpoint returning graph JSON
Create React UI components for multimodal upload, query with reasoning, summary display, and graph visualisation
Add user auth (JWT), document library per-user, query history storage
Implement real-time collaboration (WebSocket channels) on shared documents/queries (optional later)
Design and plug custom embedding strategy (domain-specific) using OpenAI fine-tuned or other models
Add export & integration endpoints (PDF/CSV export, webhook to external tools)