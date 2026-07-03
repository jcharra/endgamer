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

Documentation
-------------
Document all your changes in a file called LOGFILE.
Give an incremental change number and description.

Current task
------------
Score should never drop below 0.
Score badge should look a little nicer and not contain the word "score", but rather an icon like a golden cup.
On failure, a "retry" button should appear, allowing to restart the puzzle.
