# Match events

Every player in a [`clubs/matches`](endpoints.md#clubsmatches) response carries four
fields, `match_event_aggregate_0` to `match_event_aggregate_3`. Each is a
comma-separated list of `event_id:count` pairs:

```json
"match_event_aggregate_0": "0:2,109:3,145:5,174:19,215:21,216:5,24:17,30:8,6:1",
"match_event_aggregate_1": "97:10",
"match_event_aggregate_2": "",
"match_event_aggregate_3": ""
```

`215:21` means event 215 fired 21 times for that player in that match. An id that
appears in no bucket has a count of 0. EA does not document the ids. They are far
more detailed than the named fields: pass direction and length, possession won by
pitch third, positioning feedback and more.

!!! info "Credit"
    The mappings on this page come from the community
    [**EA FC Pro Clubs API research**](https://github.com/Interactive-63/eafc-pro-clubs-api-research)
    project, which derived them from about 51,000 FC 27 player-match rows (its
    dataset is in that repository). They are observations, not EA documentation.
    New findings and corrections belong there; this package follows its
    confirmed table.

## Using it

```python
from fc_clubs_api import FC27API

api = FC27API()
players = api.get_match_players(club_id, include_events=True)

players[["name", "passesCompleted", "passesCompletedForward",
         "possessionWonAttackingThird", "outOfPosition"]]
```

`include_events=True` adds every stat in the [confirmed table](#confirmed-high-confidence)
as a column. Where EA already sends a field with the same name (`goals`, `assists`,
`shots`), EA's value is kept.

Working from raw JSON, or want the raw counters:

```python
from fc_clubs_api.events import parse_event_aggregates, decode_events, EVENT_STATS

matches = api.get_club_matches(club_id, output="raw")
player = next(iter(matches[0]["players"][str(club_id)].values()))

parse_event_aggregates(player)   # {215: 21, 216: 5, 30: 8, ...}  every id, raw counts
decode_events(player)            # {"passesCompleted": 21, "passesCompletedForward": 8, ...}

for stat in EVENT_STATS:         # the table below, as data
    print(stat.name, stat.formula, stat.description)
```

## Confirmed (high confidence)

Decoded by `include_events=True`. Formulas with `max(0, ...)` are remainders: the
direction (or length) events don't cover every pass, so the rest is reported as
"unknown". In the research data the three direction events summed to the completed
total 98.0% of the time, and the four length events 97.7%.

Stats marked "a tag, not a partition" describe *some* goals or assists (a weak-foot
goal is also a goal); they don't add up to the total.

### Passing

| Column | Formula | Meaning |
|---|---|---|
| `passesCompleted` | `event_215` | Passes completed (excludes offside passes) |
| `passesFailed` | `event_216` | Passes failed |
| `passesCompletedForward` | `event_30` | Completed passes played forward |
| `passesCompletedBackward` | `event_32` | Completed passes played backward |
| `passesCompletedSideways` | `event_34` | Completed passes played sideways |
| `passesCompletedDirectionUnknown` | `max(0, event_215 - (event_30 + event_32 + event_34))` | Completed passes with no direction event |
| `passesCompletedShort` | `event_24` | Completed short passes |
| `passesCompletedMedium` | `event_26` | Completed medium passes |
| `passesCompletedLong` | `event_28` | Completed long passes |
| `passesCompletedCross` | `event_36` | Completed crosses (includes set pieces) |
| `passesCompletedLengthUnknown` | `max(0, event_215 - (event_24 + event_26 + event_28 + event_36))` | Completed passes with no length event |
| `passesFailedForward` | `event_31` | Failed passes played forward |
| `passesFailedBackward` | `event_33` | Failed passes played backward |
| `passesFailedSideways` | `event_35` | Failed passes played sideways |
| `passesFailedDirectionUnknown` | `max(0, event_216 - (event_31 + event_33 + event_35))` | Failed passes with no direction event |
| `passesFailedShort` | `event_25` | Failed short passes |
| `passesFailedMedium` | `event_27` | Failed medium passes |
| `passesFailedLong` | `event_29` | Failed long passes |
| `passesFailedCross` | `event_37` | Failed crosses (open play only) |
| `passesFailedLengthUnknown` | `max(0, event_216 - (event_25 + event_27 + event_29 + event_37))` | Failed passes with no length event |
| `firstTimePasses` | `event_143` | First-time passes |
| `switchesOfPlay` | `event_144` | Switch-of-play passes |
| `flairPasses` | `event_147` | Fancy / flair passes |
| `throughPasses` | `event_152` | Successful through balls |
| `offsidePasses` | `event_153` | Passes caught offside |

### Shooting and goals

| Column | Formula | Meaning |
|---|---|---|
| `shots` | `event_217 + event_218` | Shots (on + off target) |
| `shotsOnTarget` | `event_217` | Shots on target (blocked shots can fold in) |
| `shotsOnTargetInsideBox` | `event_13` | Shots on target from inside the box |
| `shotsOnTargetOutsideBox` | `event_18` | Shots on target from outside the box |
| `shotsOffTarget` | `event_218` | Shots off target |
| `shotsOffTargetInsideBox` | `event_14` | Shots off target from inside the box |
| `shotsOffTargetOutsideBox` | `event_19` | Shots off target from outside the box |
| `shotsSaved` | `event_202` | Shots saved |
| `goals` | `event_214` | Goals |
| `goalsFirstTime` | `event_128` | Goals from first-time shots (a tag, not a partition) |
| `goalsWeakFoot` | `event_131` | Goals with the weak foot (a tag, not a partition) |
| `goalsOffPost` | `event_136` | Goals in off the post (a tag, not a partition) |
| `assists` | `event_11` | Assists |
| `secondAssists` | `event_115` | Second assists |
| `throughBallAssists` | `event_118` | Assists from through balls (a tag, not a partition) |

### Dribbling

| Column | Formula | Meaning |
|---|---|---|
| `dribblesCompleted` | `event_174` | Dribbles completed |
| `dribblesCarried` | `event_97` | Dribbles carried |
| `dribblesBeat` | `max(0, event_112 - event_38)` | Players beaten without a skill move |
| `dribblesSkillMoveBeat` | `event_38` | Players beaten with a skill move |

### Defending and goalkeeping

| Column | Formula | Meaning |
|---|---|---|
| `tacklesWon` | `event_0` | Tackles won |
| `tacklesLost` | `event_1` | Tackles lost |
| `standingTacklesWon` | `event_229` | Standing tackles won |
| `slidingTacklesWon` | `event_230` | Sliding tackles won |
| `cleanTackles` | `event_164` | Successful tackles on the ball |
| `dangerousTackles` | `event_163` | Dangerous tackles |
| `interceptions` | `event_6` | Interceptions |
| `opponentsDispossessed` | `event_158` | Opponents dispossessed |
| `crossesBlocked` | `event_156` | Crosses blocked |
| `aerialDuelsWonAttacking` | `event_265` | Aerial duels won when attacking |
| `aerialDuelsWonDefending` | `event_266` | Aerial duels won when defending |
| `goodDirectionSaves` | `event_267` | Saves diving the right way |

### Possession

| Column | Formula | Meaning |
|---|---|---|
| `possessionLostDefensiveThird` | `event_105` | Possession lost in the defensive third |
| `possessionLostMiddleThird` | `event_106` | Possession lost in the middle third |
| `possessionLostAttackingThird` | `event_107` | Possession lost in the attacking third |
| `possessionWonDefensiveThird` | `event_108` | Possession won in the defensive third |
| `possessionWonMiddleThird` | `event_109` | Possession won in the middle third |
| `possessionWonAttackingThird` | `event_110` | Possession won in the attacking third |

### Discipline and set pieces

| Column | Formula | Meaning |
|---|---|---|
| `foulsConceded` | `event_2 + event_3` | Fouls conceded, all areas |
| `foulsConcededDefensiveThird` | `event_3` | Fouls conceded around the defensive third |
| `foulsWon` | `event_4` | Times this player was fouled |
| `yellowCards` | `event_95 + event_213` | Yellow cards (immediate + delayed) |
| `yellowCardsImmediate` | `event_95` | Yellow cards shown as play stopped |
| `yellowCardsDelayed` | `event_213` | Yellow cards shown after advantage was played |
| `penaltiesConceded` | `event_94` | Penalties conceded |
| `cornersConceded` | `event_10` | Corners conceded |
| `cornersTaken` | `event_145` | Corners taken |

### Positioning and match feedback

| Column | Formula | Meaning |
|---|---|---|
| `inPosition` | `event_111` | Times the feedback praised this player's positioning |
| `outOfPosition` | `event_219` | Times out of position, any severity |
| `outOfPositionSeverity1` | `event_99` | Out of position, severity 1 of 5 |
| `outOfPositionSeverity2` | `event_100` | Out of position, severity 2 of 5 |
| `outOfPositionSeverity3` | `event_101` | Out of position, severity 3 of 5 |
| `outOfPositionSeverity4` | `event_102` | Out of position, severity 4 of 5 |
| `outOfPositionSeverity5` | `event_103` | Out of position, severity 5 of 5 |
| `feedbackUseTheBall` | `event_212` | Feedback: 'Use the ball' |
| `feedbackPickYourPass` | `event_207` | Feedback: 'Pick your pass' |
| `feedbackNoGoodOption` | `event_175` | Feedback: 'No good option' |
| `feedbackGoodOptionTaken` | `event_176` | Feedback: 'Good option taken' |
| `feedbackBestOptionTaken` | `event_177` | Feedback: 'Best option taken' |
| `feedbackShouldHavePassedElsewhere` | `event_182` | Feedback: 'Should have passed elsewhere' |
| `feedbackChoseToPass` | `event_183` | Feedback: 'Chose to pass' |

Left out on purpose: `event_171` (free kicks for bad tackles). The research is
confident about what triggers it but not about what to call it.

## Partial mappings (not decoded)

Supported by the data but not accounting for every case. Use with care.

| Event | Likely meaning | Evidence |
|---|---|---|
| `event_151` | Bad / hospital passes | 4 of 4 matches checked |
| `event_121` | Tackle success indicator | Matches `event_229` 98.5% of the time |
| `event_157` | Crosses attempted, open play | Add `event_145` when a corner is crossed |
| `event_96` | Red card trigger / severe foul | 82.7% precision, 16.6% coverage |
| `event_104` | Times caught offside | Presence right, count often too low |
| `event_49`, `event_50` | Save sub-types | Each on ~18–20% of goalkeeper rows |
| `event_12`, `event_124`, `event_137` | Goals by technique | Together with `event_128`, 85.8% of goals; tags overlap |
| `event_140`, `event_93`, `event_238` | Goals by technique | ~99% precision |
| `event_123` | Chipped goals | ~99% precision |
| `event_179` | Feedback: "Should have shot" | 2 of 2 cases |
| `event_150` | Tiki-taka playstyle pass | 1 case, label uncertain |
| `event_159` | Tackle ending a dribble | 1 case, label uncertain |

## Exploratory findings (not decoded)

Events that almost never fire without a goal, so they probably tag a goal technique.
None has been tied to a named technique yet. Precision = share of firings on a goal;
recall = share of goals tagged.

| Event | Precision | Recall |
|---|---|---|
| `event_46` | ≥ 98.6% | 5.91% |
| `event_141` | ≥ 98.6% | 6.38% |
| `event_126` | ≥ 98.6% | 5.52% |
| `event_17` | ≥ 98.6% | 3.65% |
| `event_15` | ≥ 98.6% | 3.18% |
| `event_125` | ≥ 98.6% | 2.57% |
| `event_239` | ≥ 98.6% | 1.93% |
| `event_138` | ≥ 98.6% | 1.85% |
| `event_139` | ≥ 98.6% | 1.09% |
| `event_135` | ≥ 98.6% | 0.77% |
| `event_130` | ≥ 98.6% | 0.71% |
| `event_134` | ≥ 98.6% | 0.69% |
| `event_203` | 81.1% | |
| `event_173` | 68.1% | |
| `event_21` | 66.1% | |
| `event_194` | 62.3% | |
| `event_117` | 43.0% | |
| `event_48`, `event_132`, `event_122`, `event_199`, `event_168` | 100% | rare (1–124 firings) |

## Events vs EA's named fields

A live check on 2026-10-02 (59 player rows, 10 league matches) compared the decoded
stats with EA's own named fields:

- `passesmade` was usually `passesCompleted + event_153`: EA's named field
  **includes offside passes**, `event_215` does not.
- On 4 of the 59 rows the named fields were far higher than the events (for
  example `passesmade` 99 against 11 completed-pass events, with `assists` and
  `shots` also higher). The cause is unknown; the event buckets may not cover the
  whole match for some players. Treat EA's named fields as authoritative for totals,
  and the events as a breakdown.

Found something new? Contribute it to the
[research project](https://github.com/Interactive-63/eafc-pro-clubs-api-research),
with the evidence, and open an issue here to get it decoded.
