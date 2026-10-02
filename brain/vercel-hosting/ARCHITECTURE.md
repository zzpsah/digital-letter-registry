# Vercel Hosting — Architecture

```text
Browser
  -> Vercel DLR web + FastAPI serverless
      -> Supabase Auth / RLS / search
      -> Google Drive API for configured private archive objects
      -> Oracle worker later for heavy OCR/background processing
```

The Vercel application must not depend on Tailscale for end-user access.
