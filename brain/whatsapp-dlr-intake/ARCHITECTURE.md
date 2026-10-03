# Architecture

Configured WhatsApp group/chat on existing Hermes bridge → narrow Hermes plugin/hook → stage authorized PDF/JPG/PNG attachment → DLR connector runner under dedicated DLR worker identity → canonical ChannelIntakeService → private Drive original → Supabase provenance/job → dedicated worker → OCR/context/search. No second WhatsApp client/session.


## Live connector path

```text
EDU- Letters (existing Hermes WhatsApp session)
  -> Hermes pre_gateway_dispatch hook
       -> exact group-id match
       -> PDF/JPG/JPEG/PNG only
       -> protected local staging queue
       -> skip normal Hermes agent reply
  -> systemd one-minute consumer
  -> Bitwarden-backed dedicated DLR worker identity
  -> canonical ChannelIntakeService
  -> private Drive original
  -> Supabase WhatsApp provenance + processing job
  -> dedicated DLR processing worker
```

Manual web-pilot limits and WhatsApp connector limits are separate. The connector currently has a guarded cap of 20 real WhatsApp documents.
