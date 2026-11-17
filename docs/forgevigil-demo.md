# ForgeVigil demo playback

The profile animation summarizes a recorded run of ForgeVigil's offline smoke demo. It uses the fixture assessor, fictional requests, a temporary database, and the demo's scripted operator release.

[Read the complete captured output](forgevigil-demo.txt) · [Open the source demo](https://github.com/billyrdavis1985-bot/ForgeVigil/blob/fc771b36b16a49915c07891673fc4bc5ead9b3c8/forge_vigil/demo.py) · [Try the interactive walkthrough](https://forgevigil.com)

The run completed on November 17, 2026 with exit code 0 and `RESULT: PASS`.

| Step | Captured result |
| --- | --- |
| Approved public document | ALLOW, delivered |
| Restricted document | DENY, held from delivery |
| Unverified approval | REVIEW, held for a decision |
| Replay of the approved request | Replayed with no new assessment or delivery |
| Scripted operator release | Scope recheck passed, released by `demo-operator` |
| Final check | Two expected outbox items, approved public-spec bytes only, temporary state removed |

## Reproduce the run

Use the pinned ForgeVigil source at commit `fc771b36b16a49915c07891673fc4bc5ead9b3c8`. From that checkout, run the following command and save its output as `docs/forgevigil-demo.txt` in the profile repository.

```bash
python3 -B -m forge_vigil demo --assessor fixture --review
```

## Render the playback

The renderer uses Pillow 13.0.0 and DejaVu fonts from `/usr/share/fonts/truetype/dejavu` on Linux or WSL. Run it from the profile repository.

```bash
python3 -m pip install Pillow==13.0.0
python3 scripts/render_demo.py
```

The renderer validates the captured decisions, replay, release, outbox, cleanup, and final result before producing the GIF and static poster. It also renders the project map.

The README selects the static poster when the browser requests reduced motion. The full transcript provides a text version of the playback.
