# Architecture

Inbound attachment -> provenance stores private reply destination + user query/caption -> DLR worker completes -> private Oracle delivery dispatcher -> same-source chat concise reply -> email delivery package (transcript + logical Drive path + original attachment) -> Gmail sender when send authorization is available.

Public DLR code carries provider-neutral metadata only. Actual chat IDs and credentials stay private.
