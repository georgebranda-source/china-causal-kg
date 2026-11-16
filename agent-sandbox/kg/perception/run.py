"""Unattended orchestrator for the May-July 1925 perception run (PLAN.md). Launch once; no further input needed.

Phase 1 (pages already VL-OCRed): build -> smoke gate -> extract -> speaker -> normalise -> graph   (complete dataset)
Phase 2 (expansion): VL OCR of new pages (combined score >= 7) until --ocr-until -> build -> extract -> speaker ->
                     normalise -> graph. Every stage resumes from its own progress file, so phase 2 only runs new articles.

Safety: RAM guard and 10-page fresh-process OCR batches (reused from pipeline_new_scrapes.py); Ollama models unloaded before
OCR; a page failing OCR twice is skipped; OCR is abandoned (phase 1 data kept) after 3 batches in a row produce nothing;
Ollama restarted if unreachable; each stage retried once. Stop cleanly: create kg/out/perception.stop.
Progress: kg/out/perception/status.json and run.log.

Usage (from agent-sandbox/):
    .venv-kg/Scripts/python kg/perception/run.py [--ocr-until HH:MM] [--skip-ocr]
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

sys.path.insert(0, str(C.SANDBOX))
import pipeline_new_scrapes as P  # noqa: E402

P.log = C.log
PY = sys.executable
HERE = Path(__file__).resolve().parent
OLLAMA = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
OCR_UNTIL = sys.argv[sys.argv.index("--ocr-until") + 1] if "--ocr-until" in sys.argv else "09:00"
OCR_FAILED = C.OUT / "ocr_failed.txt"
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


class Stopped(Exception):
    pass


def check_stop():
    if C.STOP.exists():
        raise Stopped()


def ollama_up():
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5).read()
        return True
    except Exception:
        return False


def ensure_ollama():
    if ollama_up():
        return
    C.log("Ollama not reachable; starting ollama serve")
    subprocess.Popen([str(OLLAMA), "serve"], stdout=open(C.OUT / "ollama_serve.log", "a"), stderr=subprocess.STDOUT,
                     creationflags=getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    for _ in range(24):
        time.sleep(5)
        if ollama_up():
            return C.log("Ollama up")
    C.log("WARNING: Ollama still not reachable after 2 min")


def unload_ollama():
    if not ollama_up():
        return
    try:
        loaded = json.load(urllib.request.urlopen("http://localhost:11434/api/ps", timeout=10)).get("models", [])
        for m in loaded:
            body = json.dumps({"model": m["name"], "keep_alive": 0}).encode()
            ep = "embed" if "embed" in m["name"] else "generate"
            urllib.request.urlopen(urllib.request.Request(f"http://localhost:11434/api/{ep}", body, {"Content-Type": "application/json"}), timeout=60)
            C.log(f"unloaded {m['name']} from GPU")
    except Exception as e:
        C.log(f"unload warning: {e}")


def stage(name, args, done_marker="ALL DONE", tries=2):
    """Run a stage script; succeed if exit 0 and (when given) its output contains done_marker. Retried once."""
    for t in range(1, tries + 1):
        check_stop()
        if args[0] != "build":
            ensure_ollama()
        C.status(step=name, attempt=t)
        C.log(f"stage {name} attempt {t}")
        logf = C.OUT / f"{name.split(':')[0]}.log"
        script = {"build": "build.py", "graph": "graph.py", "speaker": "speaker.py"}.get(args[0], "stage.py")
        cmd = [PY, "-u", str(HERE / script)] + (args if script == "stage.py" else args[1:])
        with open(logf, "a", encoding="utf-8") as fh:
            fh.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} {' '.join(cmd)}\n")
            fh.flush()
            rc = subprocess.run(cmd, cwd=C.SANDBOX, stdout=fh, stderr=subprocess.STDOUT, env=ENV).returncode
        tail = logf.read_text(encoding="utf-8")[-3000:]
        ok = rc == 0 and (done_marker is None or done_marker in tail)
        C.log(f"stage {name}: exit {rc}, {'ok' if ok else 'not complete'}")
        if ok:
            return True
        if C.STOP.exists():
            raise Stopped()
        if not ollama_up():
            ensure_ollama()
    return False


def smoke_gate():
    """Extract 5 articles and run the speaker pass on them; stop the run if the output is unusable."""
    stage("smoke-extract", ["extract", "--limit", "5"], done_marker=None, tries=1)
    stage("smoke-speaker", ["speaker"], done_marker=None, tries=1)
    prog = C.load_jsonl(C.OUT / "progress.jsonl")
    spk = C.load_jsonl(C.OUT / "speakers.jsonl")
    kept = sum(c["status"] == "kept" for r in prog for c in r["claims"])
    sc = [c for r in spk for c in r["claims"]]
    problems = []
    if len(prog) < 4:
        problems.append(f"only {len(prog)} of 5 articles extracted")
    if kept and not sc:
        problems.append("speaker pass produced nothing")
    if sc and sum(c["missing"] for c in sc) > len(sc) / 2:
        problems.append("speaker output missing for most claims")
    if sc and all(c["speaker_type"] == "UNKNOWN" for c in sc):
        problems.append("all speakers UNKNOWN")
    C.log(f"smoke gate: {len(prog)} articles, {kept} kept claims, {len(sc)} speaker rows, types {dict(Counter(c['speaker_type'] for c in sc))}")
    if problems:
        C.log("SMOKE GATE FAILED: " + "; ".join(problems))
        C.status(step="stopped: smoke gate failed", problems=problems)
        raise SystemExit(1)
    C.log("smoke gate passed")


def pipeline(phase):
    C.status(phase=phase)
    test_pages = os.environ.get("PERCEPTION_TEST_PAGES")  # test mode: build only these pages (comma-separated)
    if not stage(f"build:{phase}", ["build"] + (["--only", test_pages] if test_pages else []), done_marker=None):
        C.log("build failed")
        return False
    rep = json.loads((C.OUT / "corpus_report.json").read_text(encoding="utf-8"))
    C.log(f"corpus: {rep['pages']} pages, {rep['selected']} articles selected, {rep['letters']} letters")
    C.status(corpus=rep)
    if phase == "1":
        smoke_gate()
    ok = stage(f"extract:{phase}", ["extract"])
    ok = stage(f"speaker:{phase}", ["speaker"]) and ok
    ok = stage(f"normalise:{phase}", ["normalise"]) and ok
    if not ok:
        C.log("WARNING: a model stage did not complete; building the graph from what finished")
    g = stage(f"graph:{phase}", ["graph"], done_marker=None)
    C.status(**{f"phase{phase}_graph": "built" if g else "FAILED", f"phase{phase}_done": time.strftime("%H:%M")})
    return g


def past(hhmm):
    h, m = map(int, hhmm.split(":"))
    now = time.localtime()
    return (now.tm_hour, now.tm_min) >= (h, m) and now.tm_hour < 12  # deadline is in the morning


ocr_done_this_run = set()


def ocr_new_pages():
    images = {Path(p).stem: p for p in __import__("glob").glob(str(C.REPO / "data/raw/hkpl/*/NPCM*/page_*.png"))}
    fails, empty_batches = Counter(), 0
    skipped = set(OCR_FAILED.read_text().split()) if OCR_FAILED.exists() else set()
    unload_ollama()
    while True:
        check_stop()
        todo = [p for p in C.new_ocr_pages() if not C.has_vl(p) and p not in skipped and p in images]
        if os.environ.get("PERCEPTION_TEST_OCR"):  # test mode: OCR just N pages
            todo = todo[:max(0, int(os.environ["PERCEPTION_TEST_OCR"]) - len(ocr_done_this_run))]
        C.status(step="ocr", ocr_remaining=len(todo))
        if not todo:
            return C.log("OCR: all new pages done")
        if past(OCR_UNTIL):
            return C.log(f"OCR: time limit {OCR_UNTIL} reached, {len(todo)} pages left unOCRed")
        chunk = todo[:P.VL_CHUNK]
        lst = C.OUT / "ocr_batch_current.txt"
        lst.write_text("\n".join(os.path.relpath(images[p], C.REPO).replace(os.sep, "/") for p in chunk) + "\n", encoding="utf-8")
        while P.free_ram_gb() < P.MIN_FREE_START_GB:
            C.log(f"free RAM {P.free_ram_gb():.1f} GB; waiting before OCR batch")
            time.sleep(120)
            check_stop()
        C.log(f"OCR batch: {len(chunk)} pages, {len(todo)} left, free RAM {P.free_ram_gb():.1f} GB")
        rc, oom = P.run_guarded([P.PADDLE_PY, "-u", "agent-sandbox/ocr_vl.py", f"@{os.path.relpath(lst, C.REPO)}"],
                                os.path.relpath(C.OUT / "ocr_vl.log", C.SANDBOX))
        produced = sum(C.has_vl(p) for p in chunk)
        ocr_done_this_run.update(p for p in chunk if C.has_vl(p))
        C.log(f"OCR batch exit {rc}{' (memory stop)' if oom else ''}: {produced}/{len(chunk)} pages done")
        empty_batches = 0 if produced else empty_batches + 1
        if empty_batches >= 3:
            return C.log("OCR ABANDONED: 3 batches in a row produced nothing; continuing with pages already OCRed")
        if rc != 0 and not oom:
            stuck = next((p for p in chunk if not C.has_vl(p)), None)
            if stuck:
                fails[stuck] += 1
                if fails[stuck] >= 2:
                    skipped.add(stuck)
                    with open(OCR_FAILED, "a") as fh:
                        fh.write(stuck + "\n")
                    C.log(f"OCR: {stuck} failed twice, skipped")
                else:
                    time.sleep(60)


def main():
    C.log(f"=== perception run start (pid {os.getpid()}), OCR until {OCR_UNTIL}")
    C.status(pid=os.getpid(), started=time.strftime("%Y-%m-%d %H:%M:%S"), step="start")
    try:
        pipeline("1")
        if "--skip-ocr" not in sys.argv:
            C.status(phase="2")
            ocr_new_pages()
            pipeline("2")
        C.status(step="ALL DONE")
        C.log("=== ALL DONE")
    except Stopped:
        C.status(step="stopped by stop file")
        C.log("stopped by stop file")
    except SystemExit:
        raise
    except Exception as e:
        import traceback
        C.log("CRASH: " + traceback.format_exc())
        C.status(step=f"crashed: {e}")
        raise


if __name__ == "__main__":
    main()
