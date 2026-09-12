# 0005 — Server-graded IELTS answer sheets

## Decision

Represent IELTS Listening and General Training Reading practice as a local source-paper viewer plus a web-native answer sheet. Save question responses in D1 and grade only through `IeltsService` using a verified, versioned answer-key dataset. Link wrong answers back to the learner's local 精讲 PDF.

## Context

The supplied Cambridge books and explanation books are scans whose text layers are missing or inconsistent. They are reliable visual source material, but answer data extracted from them must be normalized and validated before grading. Browser access also requires explicit local-folder permission, and the files must not be uploaded automatically.

## Alternatives

- A PDF-only viewer cannot collect answers or produce structured mistake history.
- Client-only grading exposes all score logic to presentation code and loses durable answers.
- Uploading the 7.9 GB source library to hosted storage would change the privacy and copyright boundary.
- Treating OCR output as automatically verified could create false marking from recognition errors.

## Reason

The split design keeps original layout, diagrams, and audio intact while making answers, completion, grading, and review fully interactive. It preserves the local-file boundary, gives analytics structured question-level evidence, and allows future native question rendering without changing the attempt or grading APIs.
