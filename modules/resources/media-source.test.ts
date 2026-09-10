import { describe, expect, it } from "vitest";
import { resolveMediaSource } from "./media-source";

describe("resolveMediaSource", () => {
  it.each([
    "https://www.youtube.com/watch?v=LWRWHesgcIg",
    "https://youtu.be/LWRWHesgcIg",
    "https://www.youtube.com/shorts/LWRWHesgcIg",
    "https://www.youtube-nocookie.com/embed/LWRWHesgcIg",
  ])("creates a privacy-enhanced embed for %s", (url) => {
    expect(resolveMediaSource(url)).toMatchObject({
      kind: "youtube",
      videoId: "LWRWHesgcIg",
      embedUrl: "https://www.youtube-nocookie.com/embed/LWRWHesgcIg?rel=0&cc_load_policy=0",
    });
  });

  it("recognises a direct audio file", () => {
    expect(resolveMediaSource("https://example.com/conversation.MP3?download=1")).toEqual({
      kind: "audio",
      originalUrl: "https://example.com/conversation.MP3?download=1",
    });
  });

  it("keeps podcast pages as external sources", () => {
    expect(resolveMediaSource("https://example.com/episode/12")).toEqual({
      kind: "external",
      originalUrl: "https://example.com/episode/12",
    });
  });

  it("handles a missing URL", () => {
    expect(resolveMediaSource(null)).toEqual({ kind: "none" });
  });
});
