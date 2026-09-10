export type MediaSource =
  | { kind: "youtube"; originalUrl: string; embedUrl: string; videoId: string }
  | { kind: "audio"; originalUrl: string }
  | { kind: "external"; originalUrl: string }
  | { kind: "none" };

const DIRECT_AUDIO_EXTENSIONS = new Set([".aac", ".m4a", ".mp3", ".oga", ".ogg", ".wav"]);

export function resolveMediaSource(value: string | null | undefined): MediaSource {
  const originalUrl = value?.trim();
  if (!originalUrl) return { kind: "none" };

  let url: URL;
  try {
    url = new URL(originalUrl);
  } catch {
    return { kind: "external", originalUrl };
  }

  const videoId = getYouTubeVideoId(url);
  if (videoId) {
    return {
      kind: "youtube",
      originalUrl,
      videoId,
      embedUrl: `https://www.youtube-nocookie.com/embed/${videoId}?rel=0&cc_load_policy=0`,
    };
  }

  const pathname = url.pathname.toLowerCase();
  if ([...DIRECT_AUDIO_EXTENSIONS].some((extension) => pathname.endsWith(extension))) {
    return { kind: "audio", originalUrl };
  }

  return { kind: "external", originalUrl };
}

function getYouTubeVideoId(url: URL): string | null {
  const hostname = url.hostname.toLowerCase().replace(/^www\./, "").replace(/^m\./, "");
  let candidate: string | null = null;

  if (hostname === "youtu.be") {
    candidate = url.pathname.split("/").filter(Boolean)[0] ?? null;
  } else if (hostname === "youtube.com" || hostname === "youtube-nocookie.com") {
    if (url.pathname === "/watch") candidate = url.searchParams.get("v");
    else if (/^\/(embed|shorts|live)\//.test(url.pathname)) candidate = url.pathname.split("/")[2] ?? null;
  }

  return candidate && /^[A-Za-z0-9_-]{6,15}$/.test(candidate) ? candidate : null;
}
