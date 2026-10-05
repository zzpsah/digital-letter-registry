import { createClient } from "npm:@supabase/supabase-js@2.57.4";

const json = (body: Record<string, unknown>, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return json({ error: "method not allowed" }, 405);
  const jwt = (req.headers.get("Authorization") ?? "").replace(/^Bearer\s+/i, "").trim();
  if (!jwt) return json({ error: "authentication required" }, 401);

  let body: { action?: string; archive_id?: string; user_id?: string; password?: string };
  try { body = await req.json(); } catch { return json({ error: "invalid request" }, 400); }

  const action = String(body.action ?? "").trim();
  const archiveId = String(body.archive_id ?? "").trim();
  const targetUserId = String(body.user_id ?? "").trim();
  const password = String(body.password ?? "");

  if (!["reset_password", "delete_user"].includes(action) || !archiveId || !targetUserId) {
    return json({ error: "invalid request" }, 400);
  }
  if (action === "reset_password" && (password.length < 8 || password.length > 256)) {
    return json({ error: "password must be 8 to 256 characters" }, 400);
  }

  const url = Deno.env.get("SUPABASE_URL") ?? "";
  const service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
  if (!url || !service) return json({ error: "server unavailable" }, 500);

  const admin = createClient(url, service, {
    auth: { autoRefreshToken: false, persistSession: false },
  });

  const userResult = await admin.auth.getUser(jwt);
  const caller = userResult.data.user;
  if (userResult.error || !caller) return json({ error: "invalid session" }, 401);

  const { data: callerMembership, error: callerError } = await admin
    .from("archive_members").select("user_id,role,status")
    .eq("archive_id", archiveId).eq("user_id", caller.id)
    .eq("role", "admin").eq("status", "active").limit(1).maybeSingle();
  if (callerError || !callerMembership) return json({ error: "admin access required" }, 403);

  const { data: targetMembership, error: targetError } = await admin
    .from("archive_members").select("user_id,role,status")
    .eq("archive_id", archiveId).eq("user_id", targetUserId).limit(1).maybeSingle();
  if (targetError || !targetMembership) return json({ error: "user not found" }, 404);

  if (action === "reset_password") {
    const updated = await admin.auth.admin.updateUserById(targetUserId, { password });
    if (updated.error) return json({ error: "password reset failed" }, 500);
    return json({ success: true, action: "reset_password" });
  }

  if (caller.id === targetUserId) {
    return json({ error: "you cannot delete your own admin account" }, 409);
  }

  if (String(targetMembership.role) === "admin" && String(targetMembership.status) === "active") {
    const { count, error } = await admin.from("archive_members")
      .select("user_id", { count: "exact", head: true })
      .eq("archive_id", archiveId).eq("role", "admin").eq("status", "active");
    if (error) return json({ error: "could not verify admin safety" }, 500);
    if ((count ?? 0) <= 1) return json({ error: "cannot delete the last active admin" }, 409);
  }

  const deleted = await admin.auth.admin.deleteUser(targetUserId);
  if (deleted.error) return json({ error: "user deletion failed" }, 500);
  return json({ success: true, action: "delete_user" });
});
