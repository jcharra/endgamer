Endgame trainer
---------------

This is a Flask-based webproject allowing users to improve their chess endgame skills.

All posed problems consist of 7-piece-max positions which are thus definitely solved in the syzygy database.

The player is asked to win for a given color. Multiple moves may be possible, but as soon as the player
deviates from the ideal path, he/she loses instantly. The board is darkened, a flash and a "losing" sound is played.

If the player manages to achieve mate, he/she wins.

Implementation
--------------

Flask app providing endpoints. Frontend wired up to Flask app.

Coding style
------------
Always add meaningful comments to every function.
Prefer multi line coding to terse coding for readability.
Do not comment every variable, though.

Current task
------------
None. (Last completed: email/password auth + Google OAuth backed by SQLite, a top nav bar
showing the logged-in username or "Login", and a modal for sign in/up. Apple sign-in is
stubbed only -- it needs a paid Apple Developer account and an HTTPS redirect URI, so
`/auth/apple/login` just returns a "not configured" error for now.)
