# File Ingestion & Chat Attachment Pipeline

**Date:** 2026-05-08T16:42:32.837507
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Enable file attachment support in the Milo chat UI so the tenant owner can upload files (specs, prompts, architecture docs, etc.) directly into Milo's memory and storage. When a file is attached, it is securely stored, parsed, analyzed, and written into Milo's episodic memory as structured entries — giving Milo full context of the system it is coordinating.

The pipeline consists of 4 components:

COMPONENT 1 — Chat Interface File Attachment
Enable file attachment support in the Milo chat UI. The tenant owner must be able to drag-and-drop or click-to-attach one or more files directly in the chat input area.

Supported formats:
- Documents: .pdf, .docx, .txt, .md
- Spreadsheets: .xlsx, .csv
- Presentations: .pptx
- Code/Config: .json, .yaml, .html

COMPONENT 2 — Upload Pipeline
When a file is attached and the message is sent:
1. File is securely uploaded to Milo tenant storage via storage__write — Path convention: uploads/{YYYY-MM-DD}/{original_filename}
2. File is parsed via file__read to extract full text content as Markdown
3. Milo analyzes the parsed content and extracts: document type, key facts, key decisions, architecture components, people/stakeholders, prompts or instructions, dates and timelines
4. Milo writes structured memory entries via memory__write: one summary entry for the overall document, individual entries for each key decision, architecture component, and prompt found — all tagged with metadata: { source_file, upload_date, document_type }
5. Milo responds in chat confirming: file name and size, storage path, document type detected, number of memory entries written, bullet summary of what was captured

COMPONENT 3 — Multi-File Support
Allow multiple files to be uploaded in a single message. Process each file sequentially. Provide a consolidated confirmation summary after all files are processed.

COMPONENT 4 — Duplicate Detection
Before writing to storage or memory:
1. Call memory__search with the filename and document title
2. If a matching entry exists, alert the tenant owner and ask whether to overwrite or skip
3. Do not create duplicate memory entries for the same document

## Acceptance Criteria
- [ ] Tenant owner can attach one or more files directly in the Milo chat UI
- [ ] Attached files are stored in tenant storage at uploads/{date}/{filename}
- [ ] Each file is parsed and full text is extracted successfully
- [ ] Memory entries are written for: document summary, decisions, architecture components, and prompts found in each file
- [ ] All memory entries include metadata: source_file, upload_date, document_type
- [ ] Chat confirms upload with: filename, storage path, document type, memory entry count, and bullet summary
- [ ] Multiple files uploaded in one message are all processed
- [ ] Duplicate detection works — re-uploading the same file prompts the user before overwriting
- [ ] Unsupported file formats return a clear error message listing supported formats
- [ ] Files up to 25MB are supported
- [ ] Upload fails gracefully — if parsing fails, file is still saved to storage and user is notified
- [ ] All uploads are scoped to the current tenant — no cross-tenant access possible
- [ ] End-to-end test: upload a PDF spec, confirm storage path exists, confirm memory entries written, confirm Milo can answer questions about the document content

## Technical Notes
SYSTEM CONTEXT — The following Milo tools are already live and callable:
- file__read: parse PDF, DOCX, PPTX, XLSX, TXT, MD into Markdown
- storage__read: read files from tenant storage
- storage__write: write files to tenant storage
- storage__list: list files in tenant storage
- memory__search: semantic vector search over episodic memory
- memory__write: write facts/events/decisions to memory
- document__generate: generate PDF, DOCX, PPTX from Markdown

TECHNICAL CONSTRAINTS:
1. Auth: All uploads must be authenticated via AWS Cognito — unauthenticated uploads rejected
2. Storage: Use existing Milo tenant storage layer — no new storage infrastructure
3. File size limit: 25MB per file, 100MB per upload batch
4. Encoding: All files stored as UTF-8 where applicable
5. Security: Virus/malware scan on upload before parsing (use AWS Lambda + ClamAV or equivalent)
6. No credentials or PII from file contents written to logs
7. Tenant isolation: storage paths and memory entries strictly scoped to current tenant
8. Async processing: Large files should be parsed asynchronously — do not block the chat UI
9. Error handling: Any failure in the pipeline (upload, parse, memory write) must be logged and reported to the user — do not silently fail

DEFINITION OF DONE:
- File attachment UI is live in Milo chat interface
- Upload pipeline tested end-to-end with PDF, DOCX, TXT, and XLSX
- Memory entries confirmed written and searchable via memory__search
- Duplicate detection tested and working
- Milo can answer questions about uploaded document content immediately after upload
- All acceptance criteria passing
- No regression on any existing tool
