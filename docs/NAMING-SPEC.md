# Official Archive Naming Specification

## Canonical pattern

```text
short-title__issuer__date__reference-number.ext
```

The filename is derived presentation metadata. It never replaces or mutates the immutable source identity.

## Fields

### short-title

A short, human-readable description of the letter's meaning.

Examples:

- `scholarship-guidelines`
- `inter-exam-schedule`
- `छात्रवृत्ति-निर्देश`
- `परीक्षा-फॉर्म-तिथि-विस्तार`

Hindi, English, and Hinglish are valid. Unicode letters and combining marks must be preserved.

### issuer

The issuing authority, department, institution, or board.

Examples:

- `education-department`
- `bseb`
- `शिक्षा-विभाग`
- `बिहार-विद्यालय-परीक्षा-समिति`

### date

Use the document issue date in `YYYY-MM-DD` form when confidently known.

If unavailable or uncertain, use:

```text
undated
```

Do not guess dates from upload time or unrelated surrounding text.

### reference-number

Use the official memo/reference/letter number when confidently extracted.

If unavailable or uncertain, use:

```text
no-ref
```

Reference identifiers may preserve meaningful case while filesystem-unsafe separators are normalized to hyphens.

### extension

Preserve the original file extension. The original upload remains immutable.

## Separator

The four semantic fields are separated by exactly two underscores:

```text
__
```

Hyphens are used inside a field to replace spaces or unsafe punctuation.

## Examples

```text
scholarship-guidelines__education-department__2026-10-01__REF-001.pdf
छात्रवृत्ति-निर्देश__शिक्षा-विभाग__2026-10-01__REF-001.pdf
inter-exam-schedule__education-department__undated__no-ref.pdf
udise-pen-correction__education-department__undated__no-ref.jpg
```

## Normalization rules

1. Normalize Unicode to NFC.
2. Preserve Unicode letters, digits, and combining marks.
3. Lowercase title and issuer where case applies.
4. Replace whitespace and unsafe punctuation inside fields with a single hyphen.
5. Remove leading/trailing hyphens.
6. Preserve meaningful reference-number case.
7. Use `undated` and `no-ref` placeholders instead of omitting fields.
8. Preserve the original extension.
9. Never insert a private Drive ID, URL, database key, user identifier, or other secret into the filename.

## Safety and rename workflow

Existing files are never renamed directly from generated metadata.

Required flow:

```text
existing filename
      ↓
derive candidate filename
      ↓
generate preview mapping
      ↓
human review
      ↓
explicit approval
      ↓
rename operation (future stage only)
```

The preview report must contain only the minimum identifiers required for review. Real Drive IDs/URLs must not be committed to this public repository.

## Versioning

Filename rules are derived processing logic and must have a version, for example:

```text
filename_rule_version = "official-v1"
```

Changing the naming rules later must trigger preview/reprocessing rather than mutating originals silently.
