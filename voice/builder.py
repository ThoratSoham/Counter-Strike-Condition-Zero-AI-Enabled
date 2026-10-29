import os
import json
import asyncio
import argparse
import edge_tts

async def build_library(base_dir=None, specific_teammate=None, overwrite=False, progress_callback=None):
    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    lines_file = os.path.join(base_dir, "voice", "lines.json")
    pers_dir = os.path.join(base_dir, "personalities")
    lib_dir = os.path.join(base_dir, "voice", "library")

    with open(lines_file, "r", encoding="utf-8") as f:
        lines_db = json.load(f)

    # Load personalities
    personalities = {}
    for fname in os.listdir(pers_dir):
        if fname.endswith(".json"):
            fpath = os.path.join(pers_dir, fname)
            with open(fpath, "r", encoding="utf-8") as pf:
                data = json.load(pf)
                personalities[data["id"]] = data

    tasks_to_generate = []
    for t_id, situations in lines_db.items():
        if specific_teammate and t_id != specific_teammate:
            continue
        pers = personalities.get(t_id, {})
        voice_cfg = pers.get("voice", {})
        voice_name = voice_cfg.get("voice_en", "en-US-GuyNeural")
        base_pitch = voice_cfg.get("pitch", "+0Hz")
        base_rate = voice_cfg.get("rate", "+0%")

        t_out_dir = os.path.join(lib_dir, t_id)
        os.makedirs(t_out_dir, exist_ok=True)

        for sit, lines in situations.items():
            for idx, item in enumerate(lines):
                out_path = os.path.join(t_out_dir, f"{sit}_{idx}.mp3")
                if not overwrite and os.path.exists(out_path):
                    continue

                text = item.get("text", "")
                emotion = item.get("emotion", "calm")
                pitch = base_pitch
                rate = base_rate

                if emotion in ["screaming", "hyped", "panicked"]:
                    pitch = "+4Hz"
                    rate = "+10%"
                elif emotion in ["whispering", "calm"]:
                    pitch = "-3Hz"
                    rate = "-8%"
                elif emotion in ["angry", "tilted"]:
                    pitch = "+2Hz"
                    rate = "+8%"

                tasks_to_generate.append({
                    "teammate": t_id,
                    "situation": sit,
                    "index": idx,
                    "text": text,
                    "voice": voice_name,
                    "pitch": pitch,
                    "rate": rate,
                    "out_path": out_path
                })

    total = len(tasks_to_generate)
    print(f"[VoiceBuilder] Total lines to generate: {total}")
    if total == 0:
        print("[VoiceBuilder] All voice lines are already generated! Run with --overwrite to regenerate.")
        return 0, 0

    success_count = 0
    fail_count = 0

    for i, item in enumerate(tasks_to_generate):
        try:
            print(f"[{i+1}/{total}] Generating for {item['teammate']} ({item['situation']}_{item['index']}): '{item['text']}'...")
            communicate = edge_tts.Communicate(item["text"], item["voice"], pitch=item["pitch"], rate=item["rate"])
            await communicate.save(item["out_path"])
            success_count += 1
        except Exception as e:
            print(f"[VoiceBuilder] Failed to generate line: {e}")
            fail_count += 1

        if progress_callback:
            progress_callback(i + 1, total, item["text"])

        # Small delay to keep network calls steady and gentle
        await asyncio.sleep(0.05)

    print(f"\n[VoiceBuilder] Finished! Successfully generated: {success_count}, Failed: {fail_count}")
    return success_count, fail_count

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate AI Teammates local voice line library.")
    parser.add_argument("--teammate", type=str, default=None, help="Specific teammate to build (vikram, kabir, marcus, sunny)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite already generated voice files")
    args = parser.parse_args()

    asyncio.run(build_library(specific_teammate=args.teammate, overwrite=args.overwrite))
