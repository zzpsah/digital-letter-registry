import { createClient } from "npm:@supabase/supabase-js@2.57.4";

const json = (body: Record<string, unknown>, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return json({ error: "method not allowed" }, 405);
  let body: { email?: string; password?: string; approval_token?: string };
  try { body = await req.json(); } catch { return json({ error: "invalid request" }, 400); }

  const email = String(body.email ?? "").trim().toLowerCase();
  const password = String(body.password ?? "");
  const approvalToken = String(body.approval_token ?? "").trim();
  if (!email || !email.includes("@") || email.length > 320) return json({ error: "invalid request" }, 400);
  if (password.length < 8 || password.length > 256) return json({ error: "invalid request" }, 400);
  if (!/^[0-9a-f-]{36}$/i.test(approvalToken)) return json({ error: "invalid or expired approval" }, 403);

  const url = Deno.env.get("SUPABASE_URL") ?? "";
  const service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
  if (!url || !service) return json({ error: "server unavailable" }, 500);

  const admin = createClient(url, service, {
    auth: { autoRefreshToken: false, persistSession: false },
  });

  const { data: accessRequest, error: requestError } = await admin
    .from("account_access_requests")
    .select("id,archive_id,email,status,approved_role,approved_at")
    .eq("email", email)
    .eq("approval_token", approvalToken)
    .eq("status", "approved")
    .limit(1)
    .maybeSingle();

  if (requestError || !accessRequest || !accessRequest.approved_role) {
    return json({ error: "invalid or expired approval" }, 403);
  }

  const approvedAt = Date.parse(String(accessRequest.approved_at ?? ""));
  if (!Number.isFinite(approvedAt) || Date.now() - approvedAt > 7 * 24 * 60 * 60 * 1000) {
    return json({ error: "approval expired" }, 403);
  }

  let userId = "";
  const created = await admin.auth.admin.createUser({ email, password, email_confirm: true });
  if (created.data.user) {
    userId = created.data.user.id;
  } else {
    const listed = await admin.auth.admin.listUsers({ page: 1, perPage: 1000 });
    const existing = listed.data?.users?.find((u) => (u.email ?? "").toLowerCase() === email);
    if (!existing) {
      console.error("approved account create failed", created.error?.message ?? "unknown");
      return json({ error: "account activation failed" }, 500);
    }
    userId = existing.id;
    const updated = await admin.auth.admin.updateUserById(userId, {
      password,
      email_confirm: true,
    });
    if (updated.error) {
      console.error("approved account update failed", updated.error.message);
      return json({ error: "account activation failed" }, 500);
    }
  }

  const membership = await admin.from("archive_members").upsert(
    {
      archive_id: accessRequest.archive_id,
      user_id: userId,
      role: accessRequest.approved_role,
      status: "active",
      updated_at: new Date().toISOString(),
    },
    { onConflict: "archive_id,user_id" },
  );
  if (membership.error) {
    console.error("membership activation failed", membership.error.message);
    return json({ error: "account activation failed" }, 500);
  }

  const completed = await admin
    .from("account_access_requests")
    .update({
      status: "completed",
      completed_at: new Date().toISOString(),
      approval_token: null,
      updated_at: new Date().toISOString(),
    })
    .eq("id", accessRequest.id)
    .eq("status", "approved");

  if (completed.error) {
    console.error("request completion failed", completed.error.message);
    return json({ error: "account activation failed" }, 500);
  }

  return json({ activated: true });
});
