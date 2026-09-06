const DEFAULT_API_BASE_URL = "http://localhost:8000";

function normalizeApiBaseUrl(value: string): string {
  const trimmedValue = value.trim();
  let parsedUrl: URL;

  try {
    parsedUrl = new URL(trimmedValue);
  } catch {
    throw new Error(
      "NEXT_PUBLIC_API_BASE_URL must be a valid HTTP or HTTPS URL",
    );
  }

  if (parsedUrl.protocol !== "http:" && parsedUrl.protocol !== "https:") {
    throw new Error("NEXT_PUBLIC_API_BASE_URL must use HTTP or HTTPS");
  }
  if (parsedUrl.username || parsedUrl.password) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL must not contain credentials");
  }
  if (parsedUrl.search) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL must not contain query parameters");
  }
  if (parsedUrl.hash) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL must not contain a fragment");
  }

  return parsedUrl.toString().replace(/\/+$/, "");
}

export const env = Object.freeze({
  apiBaseUrl: normalizeApiBaseUrl(
    process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL,
  ),
});
