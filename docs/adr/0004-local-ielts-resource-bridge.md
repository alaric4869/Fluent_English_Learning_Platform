# ADR 0004: Keep personal IELTS media local

## Decision

Read the learner's Cambridge IELTS books and audio through the browser File System Access API, with a directory-input fallback. Persist only practice metadata and outcomes in D1.

## Context

The supplied library is roughly 5.3GB and contains copyrighted personal-study material. Bundling it would make deployments slow, increase storage cost, and distribute source files beyond the learner's device.

## Alternatives considered

- Upload all files to object storage: convenient across devices, but requires a large upload, storage lifecycle work, and careful copyright controls.
- Embed hard-coded local paths: browsers cannot safely load arbitrary filesystem paths and the approach would not survive device changes.
- Require external public URLs: not applicable to the learner's existing books and audio.

## Consequences

The learner selects the `resources` folder on each new device and may need to renew browser permission. The cloud app remains small and private, the media never leaves the device, and a future opt-in R2 sync adapter can be added without changing IELTS practice services.
