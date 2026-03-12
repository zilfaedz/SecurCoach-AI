const SUPABASE_URL = (process.env.REACT_APP_SUPABASE_URL || "").replace(/\/+$/, "");
const SUPABASE_ANON_KEY = process.env.REACT_APP_SUPABASE_ANON_KEY || "";
const USERS_TABLE = process.env.REACT_APP_SUPABASE_USERS_TABLE || "users";

function assertSupabaseConfig() {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
    throw new Error(
      "Supabase is not configured. Set REACT_APP_SUPABASE_URL and REACT_APP_SUPABASE_ANON_KEY in react-app/.env."
    );
  }
}

async function parseSupabaseResponse(response) {
  const isJson = response.headers.get("content-type")?.includes("application/json");
  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    if (typeof payload === "object" && payload !== null) {
      throw new Error(payload.msg || payload.error_description || payload.message || "Supabase request failed.");
    }

    throw new Error(payload || "Supabase request failed.");
  }

  return payload;
}

async function supabaseFetch(path, options = {}) {
  assertSupabaseConfig();

  const response = await fetch(`${SUPABASE_URL}${path}`, {
    ...options,
    headers: {
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  return parseSupabaseResponse(response);
}

function extractUserId(payload) {
  return (
    payload?.user?.id ||
    payload?.session?.user?.id ||
    payload?.id ||
    payload?.user_id ||
    payload?.user?.identities?.[0]?.user_id ||
    ""
  );
}

async function fetchCurrentUser(accessToken) {
  if (!accessToken) {
    return null;
  }

  return supabaseFetch("/auth/v1/user", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

async function upsertUserProfile({ userId = "", email, name = "", username = "" }) {
  const normalizedEmail = email.trim().toLowerCase();
  const trimmedName = name.trim();
  const trimmedUsername = username.trim();

  const profilePayload = {
    email: normalizedEmail,
    full_name: trimmedName,
    username: trimmedUsername,
  };

  if (userId) {
    profilePayload.id = userId;
  }

  const path = userId
    ? `/rest/v1/${USERS_TABLE}`
    : `/rest/v1/${USERS_TABLE}?on_conflict=email`;

  return supabaseFetch(path, {
    method: "POST",
    headers: {
      Prefer: "resolution=merge-duplicates,return=representation",
    },
    body: JSON.stringify(profilePayload),
  });
}

export async function signInUser({ email, password }) {
  const authResult = await supabaseFetch("/auth/v1/token?grant_type=password", {
    method: "POST",
    body: JSON.stringify({
      email: email.trim().toLowerCase(),
      password,
    }),
  });

  const currentUser = await fetchCurrentUser(authResult?.access_token);
  const userId = extractUserId(currentUser || authResult);
  const metadata = currentUser?.user_metadata || authResult?.user?.user_metadata || {};

  try {
    await upsertUserProfile({
      userId,
      email: currentUser?.email || authResult?.user?.email || email,
      name: metadata?.name || "",
      username: metadata?.username || "",
    });
  } catch (error) {
    throw new Error(
      `${error.message} Your auth login worked, but the "${USERS_TABLE}" profile row could not be saved.`
    );
  }

  return authResult;
}

export async function signUpUser({ name, username, email, password }) {
  const normalizedEmail = email.trim().toLowerCase();
  const trimmedName = name.trim();
  const trimmedUsername = username.trim();

  const authResult = await supabaseFetch("/auth/v1/signup", {
    method: "POST",
    body: JSON.stringify({
      email: normalizedEmail,
      password,
      data: {
        name: trimmedName,
        username: trimmedUsername,
      },
    }),
  });

  let userId = extractUserId(authResult);

  if (!userId && authResult?.access_token) {
    const currentUser = await fetchCurrentUser(authResult.access_token);
    userId = extractUserId(currentUser);
  }

  try {
    await upsertUserProfile({
      userId,
      email: normalizedEmail,
      name: trimmedName,
      username: trimmedUsername,
    });
  } catch (error) {
    throw new Error(
      `${error.message} Make sure the "${USERS_TABLE}" table exists and allows inserts/upserts for the anon role.`
    );
  }

  return authResult;
}
