\# StockFih - Master Development Roadmap



\*\*Project:\*\* StockFih  

\*\*Type:\*\* Desktop chess application + custom chess engine  

\*\*Primary language:\*\* Python 3  

\*\*GUI framework:\*\* PySide6  

\*\*Chess rules library:\*\* python-chess  

\*\*Package manager:\*\* uv  

\*\*Target platforms:\*\* Windows 10/11 first, Fedora Linux compatibility later  

\*\*Development environment:\*\* Claude Free + user's local PC



\---



\# 1. Project Vision



StockFih is a desktop chess application with its own chess engine, personality system, player profiles, and online chess data integration.



Its defining feature is its personality.



StockFih is an arrogant, sarcastic, vulgar (in a comedic, non-targeted way), anime-referencing chess engine that comments on actual game events.



It judges the player based on rating differences, reacts to moves, remembers recurring patterns, and changes its attitude depending on the situation.



The application must remain functional even when the personality system is disabled.



\## Core principles



1\. Build the chess application before building the custom engine.

2\. Keep the GUI, chess logic, engine, personality, and online services separate.

3\. Use real chess rules and legal moves.

4\. Never fabricate chess statistics, ELO ratings, or online API data.

5\. Keep the project modular and maintainable.

6\. Prioritize Windows compatibility, then test Fedora compatibility.

7\. Do not attempt to implement the entire roadmap in one response.

8\. Complete and test each milestone before moving to the next.



\---



\# 2. Development Environment and Responsibilities



Claude Free does not have access to the user's local PC.



Claude must NOT claim to:

\- Install Python, uv, pytest, or other dependencies.

\- Execute terminal commands on the user's computer.

\- Inspect files that have not been provided.

\- Access local directories.

\- Run the application.

\- Confirm that code works without actual test results.



Instead, Claude must:

\- Generate code and explain where each file belongs.

\- Provide exact PowerShell commands when installation or execution is necessary.

\- Explain what each command does.

\- Provide Fedora equivalents when relevant.

\- Tell the user what output or error information to provide.

\- Review code, logs, screenshots, and test results supplied by the user.

\- Help diagnose errors based on the supplied evidence.



\*\*The user performs all local operations.\*\*



\## Development workflow



For every milestone:



1\. Explain the objective.

2\. Inspect the relevant project files supplied by the user.

3\. Propose the implementation.

4\. Generate or modify the required code.

5\. List every file created or modified.

6\. Provide installation or execution commands if needed.

7\. Ask the user to run the commands locally.

8\. Review the returned output and fix problems.

9\. Confirm the milestone's completion criteria.

10\. Wait for the user's approval before proceeding.



Do not silently skip milestones.



\---



\# CAMPAIGN 1: THE CHESS APPLICATION



\*\*Goal:\*\* Build a complete, usable chess application before implementing StockFih's custom engine.



\## Phase 1 - Project Foundation



\### Milestone 1.1: Environment and project setup



\- Python 3 project.

\- Initialize with uv.

\- Install PySide6.

\- Install python-chess.

\- Establish a clean source-code structure.

\- Create README.md.

\- Create ROADMAP.md.

\- Create a basic application entry point.



Suggested initial commands for the user:



```powershell

mkdir StockFih

cd StockFih

uv init

uv add pyside6 python-chess

```



\### Milestone 1.2: Architecture



Suggested structure:



```text

StockFih/

├── pyproject.toml

├── uv.lock

├── README.md

├── ROADMAP.md

├── src/

│   └── stockfih/

│       ├── main.py

│       ├── app.py

│       │

│       ├── ui/

│       │   ├── main\_window.py

│       │   ├── chessboard.py

│       │   ├── sidebar.py

│       │   ├── dialogs.py

│       │   └── settings\_window.py

│       │

│       ├── chess/

│       │   ├── game.py

│       │   ├── notation.py

│       │   └── pgn.py

│       │

│       ├── engine/

│       │   ├── base.py

│       │   └── stockfih.py

│       │

│       ├── personality/

│       │   ├── commentary.py

│       │   ├── cultural\_rules.py

│       │   ├── elo\_personality.py

│       │   ├── move\_reactions.py

│       │   ├── alien\_language.py

│       │   └── dialogue.json

│       │

│       ├── services/

│       │   ├── chesscom.py

│       │   └── rating\_service.py

│       │

│       ├── profiles/

│       │   ├── player.py

│       │   └── statistics.py

│       │

│       └── resources/

│           ├── pieces/

│           ├── sounds/

│           └── themes/

│

└── tests/

```



This is a proposed structure, not a requirement to create every file immediately.



\---



\## Phase 2 - Chessboard and Gameplay



\### Milestone 2.1: Chessboard interface



\- Display an 8x8 chessboard.

\- Render chess pieces.

\- Allow the user to select pieces.

\- Allow click-to-move.

\- Highlight selected squares.

\- Highlight legal destinations.

\- Highlight the previous move.

\- Highlight the king when in check.

\- Support board flipping.



\### Milestone 2.2: Chess rules



Use python-chess for authoritative chess-rule handling.



Implement and verify:



\- Legal moves.

\- Captures.

\- Castling.

\- En passant.

\- Pawn promotion.

\- Check.

\- Checkmate.

\- Stalemate.

\- Draw conditions.

\- Insufficient material.

\- Repetition detection.



Do not independently recreate complicated chess rules unless there is a specific reason.



\### Milestone 2.3: Game controls



\- New game.

\- Restart game.

\- Undo move.

\- Redo move.

\- Move history.

\- SAN notation.

\- Player turns.

\- Game-over detection.

\- Basic game result display.



\### Milestone 2.4: Board presentation



\- Light and dark square themes.

\- Piece themes.

\- Adjustable board size.

\- Move animations, if practical.

\- Optional sound effects.

\- Settings persistence.



\---



\## Phase 3 - Chess Game Management



\### Milestone 3.1: PGN support



\- Import PGN games.

\- Export PGN games.

\- Display move history.

\- Navigate through imported games.

\- Preserve player names and game metadata.



\### Milestone 3.2: FEN support



\- Load a position using FEN.

\- Export the current position as FEN.

\- Validate invalid FEN input.

\- Allow starting a game from a custom position.



\### Milestone 3.3: Game metadata



\- Player names.

\- Date.

\- White and black.

\- Result.

\- Opening information when available.

\- Game duration when supported.



\---



\## Phase 4 - Player Profiles and Statistics



\### Milestone 4.1: Local profiles



\- Create a player profile.

\- Set username.

\- Choose an avatar.

\- Store player preferences.

\- Store game history.



\### Milestone 4.2: Statistics



\- Total games.

\- Wins.

\- Losses.

\- Draws.

\- Win rate.

\- Rating history.

\- Peak rating.

\- Recent games.



Use SQLite for structured persistent data when appropriate.



Keep the application's internal rating separate from Chess.com ratings.



\### Milestone 4.3: StockFih rating



Establish a rating system for players competing against StockFih.



\- Use a documented rating algorithm.

\- Record rating changes.

\- Track rating history.

\- Support separate time controls if appropriate.

\- Do not invent an ELO rating before enough game data exists.



\---



\## Phase 5 - Chess.com Integration



\### Milestone 5.1: Public profile lookup



Use the official Chess.com Published-Data API (PubAPI).



Potential features:



\- Search public usernames.

\- Retrieve public profile information.

\- Retrieve public ratings.

\- Retrieve available statistics.

\- Display public game archives.



\### Milestone 5.2: Leaderboards



Retrieve and display available worldwide leaderboards:



\- Bullet.

\- Blitz.

\- Rapid.



Only display data actually supplied by the API.



\### Milestone 5.3: Public game archives



\- Retrieve available archived games.

\- Import PGNs.

\- Display game information.

\- Allow reviewing public games.



Important limitations:



\- PubAPI is primarily read-only.

\- Do not assume it can submit moves.

\- Do not assume it can change Chess.com ratings.

\- Handle unavailable data, API errors, and rate limits.

\- Never request or store a user's Chess.com password.



\---



\## Phase 6 - Application Polish



\- Dark and light themes.

\- Settings interface.

\- Sound settings.

\- Keyboard shortcuts.

\- Responsive layouts.

\- Error handling.

\- Persistent preferences.

\- Application icon.

\- Tests.

\- Windows packaging.

\- Fedora compatibility checks.



\*\*Campaign 1 completion criteria:\*\*



StockFih must be a usable chess application before the custom engine becomes the main development focus.



\---



\# CAMPAIGN 2: THE STOCKFIH ENGINE



\*\*Goal:\*\* Build a functional chess engine that can play chess independently of the GUI.



\## Phase 7 - Basic Chess Engine



\### Milestone 7.1: Engine foundation



\- Create a separate engine module.

\- Use python-chess for legal move generation.

\- Implement material evaluation.

\- Implement basic position evaluation.

\- Choose a legal move.

\- Return a move to the application.



Initial material values:



| Piece | Value |

|---|---:|

| Pawn | 100 |

| Knight | 320 |

| Bishop | 330 |

| Rook | 500 |

| Queen | 900 |

| King | Special |



\### Milestone 7.2: Search algorithm



Implement:



\- Minimax.

\- Negamax if appropriate.

\- Alpha-beta pruning.

\- Move ordering.

\- Search depth settings.



\### Milestone 7.3: Positional evaluation



Introduce:



\- Piece-square tables.

\- Mobility.

\- King safety.

\- Pawn structure.

\- Center control.

\- Piece development.



Do not add every evaluation feature simultaneously. Test each addition.



\---



\## Phase 8 - Search Improvements



Improve playing strength and search efficiency.



\### Milestone 8.1



\- Iterative deepening.

\- Transposition tables.

\- Zobrist hashing.

\- Quiescence search.

\- Better move ordering.



\### Milestone 8.2



\- Opening book.

\- Time controls.

\- Search limits.

\- Difficulty settings.

\- Search statistics.



\### Milestone 8.3: Engine benchmarking



Measure:



\- Nodes searched.

\- Nodes per second.

\- Search depth.

\- Thinking time.

\- Win/loss/draw results.

\- Tactical puzzle performance.



Never claim a particular ELO without actual testing.



\---



\# CAMPAIGN 3: STOCKFIH'S PERSONALITY



\*\*This is the defining feature of StockFih.\*\*



The personality system must be completely independent of chess move selection.



The engine decides what to play.



The personality system decides what to say.



A terrible joke must never change a good chess move.



\## Phase 9 - Commentary Architecture



\### Milestone 9.1: Event-based commentary



The personality module should receive structured game events.



Possible events:



\- Opponent plays a move.

\- StockFih plays a move.

\- Brilliant move.

\- Blunder.

\- Mistake.

\- Inaccuracy.

\- Missed winning opportunity.

\- Check.

\- Checkmate.

\- Stalemate.

\- Draw.

\- Game won.

\- Game lost.

\- Game drawn.

\- Opening recognized.

\- Repeated opening pattern.

\- Major evaluation change.



The commentary system must use actual game information.



Never claim a move is brilliant, a blunder, or a mistake without an evaluation method supporting that claim.



\### Milestone 9.2: Commentary personality



Create several modes:



\*\*Toxic Comedian\*\*

\- Cocky.

\- Sarcastic.

\- Comedically vulgar.

\- Constantly complains.

\- Makes dramatic excuses.



\*\*Professional\*\*

\- Chess-focused.

\- Minimal jokes.

\- Useful explanations.



\*\*Silent\*\*

\- No commentary.



\### Milestone 9.3: Commentary frequency



Settings:



\- Silent.

\- Normal.

\- Chaotic.

\- Unhinged.



Avoid repeating the same commentary constantly.



Add a cooldown or recent-commentary history.



\---



\## Phase 10 - ELO-Based Ego System



StockFih's personality depends on the rating difference between the player and StockFih.



Calculate:



```python

rating\_difference = player\_elo - stockfih\_elo

```



Initial personality tiers:



| Rating difference | Personality |

|---|---|

| -300 or lower | Dominant |

| -100 to -299 | Cocky |

| -99 to +99 | Rival |

| +100 to +299 | Threatened |

| +300 or higher | Existential crisis |



These are configurable design thresholds, not official chess rating categories.



\### Tier 1: Player is weaker



StockFih becomes extremely arrogant.



Examples:



\- "BRO IS PLAYING CHESS WITH A POTATO."

\- "YOUR ELO IS A CRY FOR HELP."

\- "I'M NOT EVEN USING MY FULL FISH BRAIN."



\### Tier 2: Similar rating



StockFih considers the player a rival.



Anime and JJK-inspired commentary:



\- "STAND PROUD. YOU ARE STRONG."

\- "DOMAIN EXPANSION: INFINITE BLUNDER."

\- "STAND READY FOR MY ARRIVAL, WORM."

\- "YOU AND I... WE ARE THE SAME."



\### Tier 3: Player is stronger



StockFih becomes defensive and increasingly dramatic.



Examples:



\- "OH, SO YOU THINK YOU'RE BETTER THAN ME?"

\- "YOUR RATING IS INFLATED. I DEMAND AN AUDIT."

\- "THIS IS FUCKING RIGGED."



\### Tier 4: Player is much stronger



StockFih enters an existential crisis.



Examples:



\- "I HAVE SEEN THE FACE OF GOD. IT IS PLAYING WHITE."

\- "PLEASE CONSIDER A CAREER IN SOMETHING ELSE."

\- "MY CREATOR DID NOT PREPARE ME FOR THIS."



\### Dynamic ego



The ego should also change during a match.



Examples:



\- StockFih starts confidently.

\- The player makes several strong moves.

\- StockFih becomes suspicious.

\- The player obtains a winning advantage.

\- StockFih starts making excuses.

\- StockFih finds a strong move.

\- Its ego returns.



Implement the ego as a temporary game-state variable, not as a replacement for actual ELO.



\---



\## Phase 11 - Cultural and Identity Commentary



Allow users to configure:



\- Username.

\- Country.

\- Name origin.

\- Preferred commentary language.



Do not attempt to infer someone's nationality or name origin from their username.



\### Milestone 11.1: Name origin and country



Compare manually selected country and name-origin settings.



Possible outcomes:



\*\*Matching settings\*\*



StockFih can use light language-related jokes or references.



\*\*Different settings\*\*



StockFih can make playful jokes about the unexpected combination.



Example:



\- "VIETNAM? JAPANESE NAME? BRO'S CHARACTER CREATION SETTINGS ARE RANDOMIZED."



Keep this opt-in.



Do not assume a name proves someone's nationality, ethnicity, or identity.



Do not present harmful stereotypes as facts or target people based on protected characteristics.



\### Milestone 11.2: Unknown identity mode



If the user has not configured their country or name origin:



StockFih enters Alien Mode.



Examples:



\- "ZIP ZIP ZIP ZIP ZAP ZAP ZOP."

\- "BLORP BLORP. CHECKMATE?"

\- "01001000 01000101 01001100 01010000."



Implement a small randomized alien-language generator.



It should generate harmless nonsense, not actual translations or misleading claims.



\---



\## Phase 12 - Personality Settings and Dialogue



\### Milestone 12.1: Settings



Add:



\- Personality mode.

\- Commentary frequency.

\- Profanity level.

\- ELO-based personality toggle.

\- Cultural commentary toggle.

\- Alien mode toggle.

\- Commentary language.

\- Mute button.



\### Milestone 12.2: Dialogue database



Store commentary in JSON files rather than hardcoding every line.



Example:



```json

{

&#x20; "dominant": {

&#x20;   "good\_move": \[

&#x20;     "GG FUCKING EZZZ.",

&#x20;     "I AM THE FISH."

&#x20;   ],

&#x20;   "blunder": \[

&#x20;     "BRO WHAT WAS THAT MOVE?",

&#x20;     "YOUR BRAIN BUFFERED."

&#x20;   ]

&#x20; },

&#x20; "rival": {

&#x20;   "game\_start": \[

&#x20;     "STAND PROUD. YOU ARE STRONG."

&#x20;   ]

&#x20; },

&#x20; "existential\_crisis": {

&#x20;   "game\_start": \[

&#x20;     "I HAVE A BAD FEELING ABOUT THIS."

&#x20;   ]

&#x20; }

}

```



This is an illustrative schema. Expand it as the personality system develops.



\### Milestone 12.3: Context-aware dialogue



The system should consider:



\- Current ELO tier.

\- Current ego.

\- Actual move event.

\- Game phase.

\- Opening.

\- Recent commentary.

\- Game result.



Avoid random dialogue that contradicts the current game.



\---



\# CAMPAIGN 4: LEARNING AND ADAPTATION



\## Phase 13 - Opponent Memory



\- Store previous games.

\- Track recurring openings.

\- Track common mistakes.

\- Recognize repeated player behavior.

\- Remember previous results.

\- Use stored information to influence commentary.



Example:



The player repeatedly opens with e4.



StockFih:



"OH IT'S YOU AGAIN. E4 FOR THE 47TH TIME. SEEK HELP."



Do not pretend to recognize a player when no relevant game history exists.



\## Phase 14 - Self-Improvement



Potential features:



\- Self-play.

\- Evaluation-weight tuning.

\- Opening-memory improvements.

\- Tactical pattern recognition.

\- Persistent training data.

\- Versioned evaluation parameters.

\- Benchmark comparisons.



Start with measurable, explainable improvements.



Do not claim that the engine learns automatically unless an actual learning mechanism has been implemented.



\---



\# CAMPAIGN 5: FULL INTEGRATION



\## Phase 15 - Engine and GUI Integration



\- Add StockFih as an AI opponent.

\- Add difficulty selection.

\- Add thinking-time controls.

\- Add engine analysis.

\- Add best-move display.

\- Add evaluation bar.

\- Add search information.

\- Add personality commentary panel.

\- Add commentary history.

\- Add mute and personality controls.



The engine must never block the GUI while thinking. Use an appropriate background worker or asynchronous execution design.



\## Phase 16 - Game Review



\- Analyze completed games.

\- Identify mistakes and blunders.

\- Display evaluation changes.

\- Show alternative moves.

\- Generate a summary.

\- Allow exporting analysis.



Ensure that engine evaluations are clearly distinguished from external chess platform evaluations.



\---



\# CAMPAIGN 6: TESTING AND RELEASE



\## Phase 17 - Testing



Test:



\- Chess rules.

\- Legal move generation.

\- PGN import/export.

\- FEN handling.

\- Engine move legality.

\- Search stability.

\- ELO calculations.

\- Commentary event accuracy.

\- Personality settings.

\- Data persistence.

\- API error handling.

\- GUI responsiveness.



Use pytest when appropriate, but remember that the user must install and execute it locally.



\## Phase 18 - Engine Competition



\- Self-play tournaments.

\- Controlled games against other engines.

\- Tactical puzzle benchmarks.

\- UCI interoperability.

\- Rating estimation through controlled matches.

\- Performance comparisons between versions.



Keep a record of test conditions.



Never compare ratings from different pools as though they were directly interchangeable.



\## Phase 19 - Packaging and Release



\- Windows executable.

\- Fedora installation instructions.

\- Dependency documentation.

\- User guide.

\- Configuration backup.

\- Error logs.

\- Version numbering.

\- Release notes.



\---



\# 3. Important Architecture Rules



These rules apply throughout the entire project.



1\. The GUI must not contain chess-engine search logic.

2\. The chess-rule layer must not depend on the GUI.

3\. The engine must not depend on the personality system.

4\. The personality system must not determine chess moves.

5\. Online services must be separate from local game logic.

6\. Settings and game data must persist safely.

7\. Avoid unnecessary dependencies.

8\. Use pathlib for cross-platform filesystem paths.

9\. Avoid Windows-only assumptions in core logic.

10\. Keep API credentials and sensitive information out of source control.

11\. Validate external data before using it.

12\. Prefer readable, maintainable code over unnecessarily clever code.



\---



\# 4. Claude Free Operating Instructions



Claude must follow these rules:



\- Work on ONE milestone at a time.

\- Do not generate the entire application in one response.

\- Do not jump ahead to the engine while the application foundation is unfinished.

\- Do not assume access to the user's PC.

\- Do not claim to have executed commands.

\- Do not invent test results.

\- Do not invent API endpoints or capabilities.

\- Do not overwrite unrelated files.

\- Do not remove working features without explaining why.

\- Ask for relevant files when necessary.

\- Keep code changes focused.

\- Explain any architectural changes before implementing them.

\- Provide exact local commands for the user to run.

\- Wait for the user's test results.

\- Fix reported errors before moving forward.



If a task is too large for one response, divide it into smaller steps.



If context becomes limited, summarize the current project state, completed milestones, known bugs, and next milestone.



\---



\# 5. Definition of Success



StockFih is successful when it has:



\- A complete desktop chess application.

\- A functional custom chess engine.

\- Measurable playing strength.

\- A context-aware commentary system.

\- An ELO-based ego system.

\- Configurable personality and cultural commentary.

\- An optional alien-language mode.

\- Player profiles and statistics.

\- Optional Chess.com public-data integration.

\- Reliable Windows support and documented Fedora compatibility.



\*\*Final vision:\*\*



A chess engine that can calculate a position, recognize that its opponent is destroying it, and confidently announce:



"THIS IS A TEMPORARY SETBACK. I AM STILL THE HONORED ONE."



\*\*STOCKFIH. THE FISH WITH AN UNJUSTIFIABLY HIGH EGO.\*\* 🐟

