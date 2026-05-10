-- TODO: replace placeholder video_ids with real URLs once pre-processing runs.
INSERT INTO videos (
    video_id,
    title,
    duration_seconds,
    uploader,
    metadata
  )
VALUES (
    'dQw4w9WgXcQ',
    'Placeholder (replace with real lecture)',
    3600,
    'TBD',
    '{}'
  ),
  (
    'placeholder2',
    'Placeholder (replace with real lecture)',
    3600,
    'TBD',
    '{}'
  ),
  (
    'placeholder3',
    'Placeholder (replace with real lecture)',
    3600,
    'TBD',
    '{}'
  ) ON CONFLICT (video_id) DO NOTHING;