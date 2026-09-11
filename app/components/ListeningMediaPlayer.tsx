import { resolveMediaSource } from "../../modules/resources/media-source";

export function ListeningMediaPlayer({ title, source, url }: { title: string; source: string; url: string | null }) {
  const media = resolveMediaSource(url);

  if (media.kind === "youtube") {
    return (
      <section className="listening-media-card">
        <div className="listening-media-head">
          <div><span>REAL CONVERSATION · YOUTUBE</span><strong>{source}</strong></div>
          <a href={media.originalUrl} target="_blank" rel="noreferrer">Open on YouTube ↗</a>
        </div>
        <div className="youtube-frame">
          <iframe
            src={media.embedUrl}
            title={`${title} listening video`}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            referrerPolicy="strict-origin-when-cross-origin"
            allowFullScreen
          />
        </div>
        <p className="media-study-tip"><strong>First pass:</strong> keep CC off. <strong>Second pass:</strong> turn on English CC, then pause and replay difficult parts.</p>
      </section>
    );
  }

  if (media.kind === "audio") {
    return (
      <section className="listening-media-card audio-media-card">
        <div className="listening-media-head"><div><span>REAL AUDIO</span><strong>{source}</strong></div><a href={media.originalUrl} target="_blank" rel="noreferrer">Open audio ↗</a></div>
        {/* This source has no timed-caption file; the lesson transcript is displayed beside the player. */}
        {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
        <audio controls preload="metadata" src={media.originalUrl}>Your browser cannot play this audio. Use the open-audio link instead.</audio>
        <p className="media-study-tip"><strong>First pass:</strong> listen without the transcript. Then replay short sections while checking the text.</p>
      </section>
    );
  }

  if (media.kind === "external") {
    return (
      <section className="listening-media-card external-media-card">
        <div><span>REAL MEDIA · EXTERNAL SOURCE</span><strong>{source}</strong><p>This provider cannot be embedded here. Keep this lesson open and play the original recording in a new tab.</p></div>
        <a className="primary-button" href={media.originalUrl} target="_blank" rel="noreferrer">Open original recording <span>↗</span></a>
      </section>
    );
  }

  return (
    <section className="listening-media-card missing-media-card">
      <div><span>REAL MEDIA NEEDED</span><strong>No recording is linked to this lesson yet</strong><p>Edit this resource in the Library and add a YouTube, MP3, M4A, OGG or WAV URL.</p></div>
    </section>
  );
}
