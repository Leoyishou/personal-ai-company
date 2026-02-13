# Sight-Singing Tool Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a web-based sight-singing practice tool that loads MusicXML files, renders them as jianpu (numbered musical notation), and plays them back with piano sound and metronome at adjustable tempo.

**Architecture:** Vanilla JS + Vite. MusicXML parsed via DOMParser into a flat NoteSequence array. Tone.js handles all audio (piano Sampler from Salamander CDN, metronome Loop, Transport for tempo). SVG renders jianpu notation with highlight sync.

**Tech Stack:** Vite, Tone.js, Vitest (tests), vanilla JS, SVG

---

## Project Structure

```
inbox/sight-singing/
├── index.html
├── package.json
├── vite.config.js
├── src/
│   ├── main.js           # Entry: wires everything together
│   ├── parser.js          # MusicXML -> NoteSequence
│   ├── jianpu.js          # NoteSequence -> SVG rendering
│   ├── audio.js           # Tone.js piano + metronome + transport
│   └── style.css          # Styles
├── test/
│   ├── parser.test.js     # Parser unit tests
│   └── fixtures/
│       └── twinkle.musicxml
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `inbox/sight-singing/package.json`
- Create: `inbox/sight-singing/index.html`
- Create: `inbox/sight-singing/vite.config.js`
- Create: `inbox/sight-singing/src/main.js`
- Create: `inbox/sight-singing/src/style.css`
- Create: `inbox/sight-singing/sessionInfo.md`

**Step 1: Create project directory and package.json**

```bash
mkdir -p /Users/liuyishou/usr/pac/product-bu/inbox/sight-singing/src
mkdir -p /Users/liuyishou/usr/pac/product-bu/inbox/sight-singing/test/fixtures
```

Write `package.json`:
```json
{
  "name": "sight-singing",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

**Step 2: Install dependencies**

```bash
cd /Users/liuyishou/usr/pac/product-bu/inbox/sight-singing
npm install tone
npm install -D vite vitest
```

**Step 3: Create index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>视唱练习</title>
  <link rel="stylesheet" href="/src/style.css">
</head>
<body>
  <div id="app">
    <header id="info-bar">
      <span id="key-sig">1=C</span>
      <span id="time-sig">4/4</span>
      <span id="bpm-display">♩=80</span>
      <label id="upload-label">
        上传乐谱
        <input type="file" id="file-input" accept=".musicxml,.xml" hidden>
      </label>
    </header>

    <main id="score-area">
      <div id="empty-state">拖拽或点击上方按钮上传 MusicXML 文件</div>
      <svg id="jianpu-svg"></svg>
    </main>

    <footer id="controls">
      <div id="transport-row">
        <button id="btn-restart" title="回到开头">⏮</button>
        <button id="btn-play" title="播放/暂停 (空格)">▶</button>
        <input type="range" id="progress" min="0" max="100" value="0">
        <span id="time-display">0:00</span>
      </div>
      <div id="speed-row">
        <span>速度:</span>
        <button id="btn-slower">−</button>
        <input type="range" id="bpm-slider" min="20" max="200" value="80">
        <button id="btn-faster">+</button>
        <span id="bpm-value">♩=80</span>
      </div>
      <div id="metro-row">
        <label><input type="checkbox" id="metro-toggle" checked> 节拍器</label>
        <span>音量:</span>
        <input type="range" id="volume" min="0" max="100" value="70">
      </div>
    </footer>
  </div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

**Step 4: Create minimal style.css**

```css
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, "Helvetica Neue", "PingFang SC", sans-serif;
  background: #fafafa;
  color: #333;
}

#app {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

#info-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  font-size: 15px;
}

#info-bar span { font-weight: 500; }

#upload-label {
  margin-left: auto;
  padding: 6px 14px;
  background: #4a90d9;
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

#score-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px 16px;
  background: #fff;
}

#empty-state {
  text-align: center;
  color: #999;
  margin-top: 120px;
  font-size: 15px;
}

#jianpu-svg { display: none; width: 100%; }

#controls {
  padding: 12px 16px;
  background: #f5f5f5;
  border-top: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

#transport-row, #speed-row, #metro-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

#transport-row button, #speed-row button {
  width: 36px;
  height: 36px;
  border: 1px solid #ccc;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 16px;
}

#progress, #bpm-slider, #volume {
  flex: 1;
  height: 6px;
}

.note-highlight {
  fill: #4a90d9;
  opacity: 0.2;
  rx: 4;
}
```

**Step 5: Create placeholder main.js**

```js
// src/main.js - Entry point, will wire modules together
console.log('Sight-singing tool loaded');
```

**Step 6: Create vite.config.js**

```js
import { defineConfig } from 'vite';

export default defineConfig({
  root: '.',
  test: {
    environment: 'node',
  },
});
```

**Step 7: Create sessionInfo.md**

```markdown
# Session Info

- **Created**: 2026-02-13
- **Purpose**: 视唱练习工具 - MusicXML 简谱播放器
```

**Step 8: Verify dev server starts**

```bash
cd /Users/liuyishou/usr/pac/product-bu/inbox/sight-singing
npx vite --open
```
Expected: Browser opens, shows the UI skeleton with upload button and controls.

**Step 9: Commit**

```bash
git add -A
git commit -m "feat: scaffold sight-singing project with Vite + Tone.js"
```

---

### Task 2: MusicXML Parser (with tests)

**Files:**
- Create: `test/fixtures/twinkle.musicxml`
- Create: `test/parser.test.js`
- Create: `src/parser.js`

**Step 1: Create test fixture - Twinkle Twinkle (first 4 measures)**

Write `test/fixtures/twinkle.musicxml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <part-list>
    <score-part id="P1"><part-name>Piano</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key><fifths>0</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time>
      </attributes>
      <direction placement="above">
        <direction-type>
          <metronome><beat-unit>quarter</beat-unit><per-minute>120</per-minute></metronome>
        </direction-type>
        <sound tempo="120"/>
      </direction>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>G</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>G</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
    </measure>
    <measure number="2">
      <note><pitch><step>A</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>A</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>G</step><octave>4</octave></pitch><duration>2</duration><type>half</type></note>
    </measure>
    <measure number="3">
      <note><pitch><step>F</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>F</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>E</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>E</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
    </measure>
    <measure number="4">
      <note><pitch><step>D</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>D</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>2</duration><type>half</type></note>
    </measure>
  </part>
</score-partwise>
```

**Step 2: Write failing parser tests**

Write `test/parser.test.js`:
```js
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { resolve } from 'path';
import { parseMusicXML } from '../src/parser.js';

const xml = readFileSync(resolve(__dirname, 'fixtures/twinkle.musicxml'), 'utf-8');

describe('parseMusicXML', () => {
  it('extracts metadata', () => {
    const result = parseMusicXML(xml);
    expect(result.key).toBe('C');
    expect(result.keyFifths).toBe(0);
    expect(result.timeBeats).toBe(4);
    expect(result.timeBeatType).toBe(4);
    expect(result.tempo).toBe(120);
  });

  it('parses correct number of notes', () => {
    const result = parseMusicXML(xml);
    // m1: 4 notes, m2: 3 notes, m3: 4 notes, m4: 3 notes = 14
    expect(result.notes.length).toBe(14);
  });

  it('parses first note as C4', () => {
    const { notes } = parseMusicXML(xml);
    expect(notes[0].step).toBe('C');
    expect(notes[0].octave).toBe(4);
    expect(notes[0].midi).toBe(60);
    expect(notes[0].type).toBe('quarter');
    expect(notes[0].measure).toBe(1);
    expect(notes[0].isRest).toBe(false);
  });

  it('computes jianpu numbers in C major', () => {
    const { notes } = parseMusicXML(xml);
    // C=1, G=5, A=6, F=4, E=3, D=2
    expect(notes[0].jianpu).toBe(1);  // C
    expect(notes[2].jianpu).toBe(5);  // G
    expect(notes[4].jianpu).toBe(6);  // A
    expect(notes[7].jianpu).toBe(4);  // F
    expect(notes[9].jianpu).toBe(3);  // E
    expect(notes[11].jianpu).toBe(2); // D
  });

  it('computes octave shift relative to base octave', () => {
    const { notes } = parseMusicXML(xml);
    // All notes in octave 4 (C major base = octave 4), so shift = 0
    notes.forEach(n => expect(n.octaveShift).toBe(0));
  });

  it('computes beat positions', () => {
    const { notes } = parseMusicXML(xml);
    // m1: beat 0, 1, 2, 3
    expect(notes[0].beat).toBe(0);
    expect(notes[1].beat).toBe(1);
    expect(notes[2].beat).toBe(2);
    expect(notes[3].beat).toBe(3);
    // m2: beat 4, 5, 6 (half note occupies beats 6-7)
    expect(notes[4].beat).toBe(4);
    expect(notes[5].beat).toBe(5);
    expect(notes[6].beat).toBe(6);
  });

  it('computes duration in beats', () => {
    const { notes } = parseMusicXML(xml);
    expect(notes[0].durationBeats).toBe(1);  // quarter
    expect(notes[6].durationBeats).toBe(2);  // half
  });
});
```

**Step 3: Run tests to verify they fail**

```bash
cd /Users/liuyishou/usr/pac/product-bu/inbox/sight-singing
npx vitest run
```
Expected: FAIL - `parseMusicXML` is not exported.

**Step 4: Implement parser**

Write `src/parser.js`:
```js
// Step-to-semitone offset from C (within one octave)
const STEP_SEMITONES = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };

// Key signature fifths -> tonic step name
const FIFTHS_TO_KEY = {
  '-7': 'Cb', '-6': 'Gb', '-5': 'Db', '-4': 'Ab', '-3': 'Eb', '-2': 'Bb', '-1': 'F',
  '0': 'C', '1': 'G', '2': 'D', '3': 'A', '4': 'E', '5': 'B', '6': 'F#', '7': 'C#'
};

// Tonic step -> base MIDI note (octave 4)
const KEY_BASE_MIDI = {
  'C': 60, 'G': 67, 'D': 62, 'A': 69, 'E': 64, 'B': 71,
  'F': 65, 'Bb': 70, 'Eb': 63, 'Ab': 68, 'Db': 61, 'Gb': 66,
  'F#': 66, 'C#': 61, 'Cb': 59
};

function stepToMidi(step, octave, alter = 0) {
  return STEP_SEMITONES[step] + (octave + 1) * 12 + alter;
}

function midiToJianpu(midi, keyBaseMidi) {
  // Semitone offset from tonic
  const offset = ((midi - keyBaseMidi) % 12 + 12) % 12;
  // Major scale intervals: 0=1, 2=2, 4=3, 5=4, 7=5, 9=6, 11=7
  const SCALE_MAP = { 0: 1, 2: 2, 4: 3, 5: 4, 7: 5, 9: 6, 11: 7 };
  return SCALE_MAP[offset] || 1; // Fallback to 1 for chromatic notes
}

function midiToOctaveShift(midi, keyBaseMidi) {
  // How many octaves away from the base octave (octave 4 range)
  const diff = midi - keyBaseMidi;
  if (diff >= 0) return Math.floor(diff / 12);
  return -Math.ceil(-diff / 12);
}

export function parseMusicXML(xmlString) {
  const parser = typeof DOMParser !== 'undefined'
    ? new DOMParser()
    : new (await import('xmldom')).DOMParser(); // Won't actually be needed
  // For Node.js test environment, use a simple regex-based approach or jsdom
  // But vitest can use jsdom. Let's use a universal approach.

  let doc;
  if (typeof DOMParser !== 'undefined') {
    doc = new DOMParser().parseFromString(xmlString, 'text/xml');
  } else {
    // Node environment (vitest) - use built-in XML parsing
    const { JSDOM } = await import('jsdom');
    const dom = new JSDOM(xmlString, { contentType: 'text/xml' });
    doc = dom.window.document;
  }

  // Extract metadata from first measure's attributes
  const attrs = doc.querySelector('attributes');
  const divisions = parseInt(attrs?.querySelector('divisions')?.textContent || '1');
  const fifths = parseInt(attrs?.querySelector('key fifths')?.textContent || '0');
  const beats = parseInt(attrs?.querySelector('time beats')?.textContent || '4');
  const beatType = parseInt(attrs?.querySelector('time beat-type')?.textContent || '4');

  const key = FIFTHS_TO_KEY[String(fifths)] || 'C';
  const keyBaseMidi = KEY_BASE_MIDI[key] || 60;

  // Extract tempo
  let tempo = 120;
  const soundEl = doc.querySelector('sound[tempo]');
  if (soundEl) tempo = parseInt(soundEl.getAttribute('tempo'));

  // Parse all notes
  const notes = [];
  let currentBeat = 0;
  let currentMeasure = 0;

  const measures = doc.querySelectorAll('measure');
  measures.forEach(measure => {
    currentMeasure = parseInt(measure.getAttribute('number'));
    let measureBeatStart = currentBeat;

    // Check for attributes change mid-piece (divisions might change)
    const mAttrs = measure.querySelector('attributes');
    const mDivisions = mAttrs?.querySelector('divisions');
    const localDivisions = mDivisions ? parseInt(mDivisions.textContent) : divisions;

    const noteEls = measure.querySelectorAll('note');
    noteEls.forEach(noteEl => {
      const isRest = noteEl.querySelector('rest') !== null;
      const duration = parseInt(noteEl.querySelector('duration')?.textContent || '1');
      const type = noteEl.querySelector('type')?.textContent || 'quarter';
      const dotted = noteEl.querySelector('dot') !== null;
      const durationBeats = duration / localDivisions;

      let step = '', octave = 4, alter = 0, midi = 0, jianpu = 0, octaveShift = 0;

      if (!isRest) {
        step = noteEl.querySelector('pitch step')?.textContent || 'C';
        octave = parseInt(noteEl.querySelector('pitch octave')?.textContent || '4');
        const alterEl = noteEl.querySelector('pitch alter');
        alter = alterEl ? parseInt(alterEl.textContent) : 0;
        midi = stepToMidi(step, octave, alter);
        jianpu = midiToJianpu(midi, keyBaseMidi);
        octaveShift = midiToOctaveShift(midi, keyBaseMidi);
      }

      notes.push({
        step, octave, alter, midi, type, isRest, dotted,
        jianpu, octaveShift,
        measure: currentMeasure,
        beat: currentBeat,
        durationBeats,
      });

      currentBeat += durationBeats;
    });
  });

  return { key, keyFifths: fifths, timeBeats: beats, timeBeatType: beatType, tempo, divisions, notes };
}
```

**Important:** The parser uses dynamic import for jsdom in Node. Update vite.config.js test environment:

Update `vite.config.js`:
```js
import { defineConfig } from 'vite';

export default defineConfig({
  root: '.',
  test: {
    environment: 'jsdom',
  },
});
```

Install jsdom: `npm install -D jsdom`

Then simplify `parseMusicXML` to always use `DOMParser` (jsdom provides it in test env):

Replace the conditional parsing block in `src/parser.js` with:
```js
export function parseMusicXML(xmlString) {
  const doc = new DOMParser().parseFromString(xmlString, 'text/xml');
  // ... rest of parsing logic
```

**Step 5: Run tests to verify they pass**

```bash
npx vitest run
```
Expected: All 7 tests PASS.

**Step 6: Commit**

```bash
git add src/parser.js test/
git commit -m "feat: MusicXML parser with jianpu conversion"
```

---

### Task 3: Audio Engine (Piano + Metronome)

**Files:**
- Create: `src/audio.js`

**Step 1: Implement audio module**

Write `src/audio.js`:
```js
import * as Tone from 'tone';

let piano = null;
let metronomeSynth = null;
let metronomeLoop = null;
let metronomeEnabled = true;
let noteEvents = []; // Scheduled Transport event IDs
let onNoteCallback = null; // Called with note index during playback

export async function initAudio() {
  await Tone.start();

  piano = new Tone.Sampler({
    urls: {
      A0: 'A0.mp3', C1: 'C1.mp3', 'D#1': 'Ds1.mp3', 'F#1': 'Fs1.mp3',
      A1: 'A1.mp3', C2: 'C2.mp3', 'D#2': 'Ds2.mp3', 'F#2': 'Fs2.mp3',
      A2: 'A2.mp3', C3: 'C3.mp3', 'D#3': 'Ds3.mp3', 'F#3': 'Fs3.mp3',
      A3: 'A3.mp3', C4: 'C4.mp3', 'D#4': 'Ds4.mp3', 'F#4': 'Fs4.mp3',
      A4: 'A4.mp3', C5: 'C5.mp3', 'D#5': 'Ds5.mp3', 'F#5': 'Fs5.mp3',
      A5: 'A5.mp3', C6: 'C6.mp3', 'D#6': 'Ds6.mp3', 'F#6': 'Fs6.mp3',
      A7: 'A7.mp3', C8: 'C8.mp3',
    },
    release: 1,
    baseUrl: 'https://tonejs.github.io/audio/salamander/',
  }).toDestination();

  metronomeSynth = new Tone.MembraneSynth({
    pitchDecay: 0.01,
    octaves: 6,
    envelope: { attack: 0.001, decay: 0.1, sustain: 0, release: 0.1 },
    volume: -10,
  }).toDestination();

  await Tone.loaded();
  return piano;
}

export function scheduleNotes(notes, onNote) {
  clearSchedule();
  onNoteCallback = onNote;

  notes.forEach((note, index) => {
    const timeInBeats = `0:${note.beat}:0`;
    const durationInBeats = `0:${note.durationBeats}:0`;

    const eventId = Tone.getTransport().schedule((time) => {
      if (!note.isRest) {
        const noteName = Tone.Frequency(note.midi, 'midi').toNote();
        piano.triggerAttackRelease(noteName, durationInBeats, time);
      }
      // Notify UI on the main thread
      Tone.getDraw().schedule(() => {
        if (onNoteCallback) onNoteCallback(index);
      }, time);
    }, timeInBeats);

    noteEvents.push(eventId);
  });
}

export function setupMetronome(beatsPerMeasure) {
  if (metronomeLoop) metronomeLoop.dispose();

  metronomeLoop = new Tone.Loop((time) => {
    if (metronomeEnabled) {
      metronomeSynth.triggerAttackRelease('C2', '32n', time);
    }
  }, '4n');
  metronomeLoop.start(0);
}

export function setMetronomeEnabled(enabled) {
  metronomeEnabled = enabled;
}

export function setBpm(bpm) {
  Tone.getTransport().bpm.value = bpm;
}

export function play() {
  Tone.getTransport().start();
}

export function pause() {
  Tone.getTransport().pause();
}

export function stop() {
  Tone.getTransport().stop();
}

export function seekToBeat(beat) {
  Tone.getTransport().position = `0:${beat}:0`;
}

export function setVolume(db) {
  Tone.getDestination().volume.value = db;
}

export function getTransportState() {
  return Tone.getTransport().state; // 'started' | 'stopped' | 'paused'
}

export function getTotalBeats(notes) {
  if (notes.length === 0) return 0;
  const last = notes[notes.length - 1];
  return last.beat + last.durationBeats;
}

function clearSchedule() {
  noteEvents.forEach(id => Tone.getTransport().clear(id));
  noteEvents = [];
  onNoteCallback = null;
}
```

**Step 2: Test manually in browser**

Add to `src/main.js` temporarily:
```js
import { initAudio, scheduleNotes, setupMetronome, setBpm, play } from './audio.js';

// Quick test: play C major scale
document.getElementById('btn-play').addEventListener('click', async () => {
  await initAudio();
  const testNotes = [
    { midi: 60, beat: 0, durationBeats: 1, isRest: false },
    { midi: 62, beat: 1, durationBeats: 1, isRest: false },
    { midi: 64, beat: 2, durationBeats: 1, isRest: false },
    { midi: 65, beat: 3, durationBeats: 1, isRest: false },
    { midi: 67, beat: 4, durationBeats: 1, isRest: false },
    { midi: 69, beat: 5, durationBeats: 1, isRest: false },
    { midi: 71, beat: 6, durationBeats: 1, isRest: false },
    { midi: 72, beat: 7, durationBeats: 1, isRest: false },
  ];
  setBpm(80);
  setupMetronome(4);
  scheduleNotes(testNotes, (i) => console.log('Playing note', i));
  play();
});
```

```bash
npx vite
```
Expected: Click play button -> hear C major scale with piano sound + metronome clicks.

**Step 3: Commit**

```bash
git add src/audio.js src/main.js
git commit -m "feat: audio engine with piano sampler and metronome"
```

---

### Task 4: Jianpu Renderer (SVG)

**Files:**
- Create: `src/jianpu.js`

**Step 1: Implement jianpu SVG renderer**

Write `src/jianpu.js`:
```js
const NOTE_WIDTH = 40;    // Width per note cell
const ROW_HEIGHT = 60;    // Height per row
const NOTES_PER_ROW = 16; // Max notes before wrapping
const LEFT_MARGIN = 20;
const TOP_MARGIN = 40;

let svgEl = null;
let highlightRect = null;
let notePositions = []; // {x, y, width} for each note

export function renderJianpu(svg, scoreData) {
  svgEl = svg;
  svg.innerHTML = '';
  notePositions = [];

  const { notes, key, timeBeats, timeBeatType } = scoreData;

  // Header: key + time signature
  const header = createText(`1=${key}  ${timeBeats}/${timeBeatType}`, LEFT_MARGIN, 24, '15px', '#666');
  svg.appendChild(header);

  let x = LEFT_MARGIN;
  let y = TOP_MARGIN + ROW_HEIGHT / 2;
  let notesInRow = 0;
  let lastMeasure = 0;

  notes.forEach((note, i) => {
    // New measure: add bar line
    if (note.measure !== lastMeasure && notesInRow > 0) {
      const barLine = createLine(x, y - 16, x, y + 16, '#ccc');
      svg.appendChild(barLine);
      x += 8;
      lastMeasure = note.measure;
    }
    if (i === 0) lastMeasure = note.measure;

    // Wrap to next row
    if (notesInRow >= NOTES_PER_ROW) {
      x = LEFT_MARGIN;
      y += ROW_HEIGHT;
      notesInRow = 0;
    }

    // Record position for highlighting
    const cellWidth = NOTE_WIDTH * note.durationBeats;
    notePositions.push({ x, y: y - 20, width: cellWidth, height: 40, rowY: y });

    // Draw the note
    if (note.isRest) {
      const text = createText('0', x + cellWidth / 2, y, '20px', '#999');
      text.setAttribute('text-anchor', 'middle');
      svg.appendChild(text);
    } else {
      // Main jianpu number
      const text = createText(String(note.jianpu), x + cellWidth / 2, y, '22px', '#333');
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('font-weight', '500');
      svg.appendChild(text);

      // Octave dots (above for high, below for low)
      for (let d = 0; d < Math.abs(note.octaveShift); d++) {
        const dotY = note.octaveShift > 0
          ? y - 18 - d * 6   // Above
          : y + 12 + d * 6;  // Below
        const dot = createCircle(x + cellWidth / 2, dotY, 2, '#333');
        svg.appendChild(dot);
      }

      // Duration underlines (eighth = 1 line, sixteenth = 2 lines)
      const lines = note.type === 'eighth' ? 1
        : note.type === '16th' ? 2
        : 0;
      for (let l = 0; l < lines; l++) {
        const lineY = y + 14 + l * 4;
        const ul = createLine(
          x + cellWidth / 2 - 8, lineY,
          x + cellWidth / 2 + 8, lineY,
          '#333', 1.5
        );
        svg.appendChild(ul);
      }

      // Dotted note marker
      if (note.dotted) {
        const dotX = x + cellWidth / 2 + 10;
        const dot = createCircle(dotX, y - 2, 2, '#333');
        svg.appendChild(dot);
      }
    }

    // Extension dash for half/whole notes (fill remaining beats)
    if (note.durationBeats > 1 && !note.isRest) {
      for (let d = 1; d < note.durationBeats; d++) {
        const dashX = x + NOTE_WIDTH * d + NOTE_WIDTH / 2;
        const dash = createText('−', dashX, y, '20px', '#999');
        dash.setAttribute('text-anchor', 'middle');
        svg.appendChild(dash);
      }
    }

    x += cellWidth;
    notesInRow += note.durationBeats;
  });

  // End barline
  const endBar = createLine(x + 4, y - 16, x + 4, y + 16, '#333', 2);
  svg.appendChild(endBar);

  // Set SVG dimensions
  const totalHeight = y + ROW_HEIGHT;
  svg.setAttribute('viewBox', `0 0 800 ${totalHeight}`);
  svg.style.height = `${totalHeight}px`;
  svg.style.display = 'block';

  // Create highlight rectangle (initially hidden)
  highlightRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  highlightRect.setAttribute('class', 'note-highlight');
  highlightRect.setAttribute('width', '0');
  highlightRect.setAttribute('height', '0');
  svg.insertBefore(highlightRect, svg.firstChild);
}

export function highlightNote(index) {
  if (!highlightRect || !notePositions[index]) return;
  const pos = notePositions[index];
  highlightRect.setAttribute('x', pos.x);
  highlightRect.setAttribute('y', pos.y);
  highlightRect.setAttribute('width', pos.width);
  highlightRect.setAttribute('height', pos.height);

  // Auto-scroll: ensure the highlighted note's row is visible
  const scoreArea = document.getElementById('score-area');
  if (scoreArea) {
    const rowTop = pos.rowY - ROW_HEIGHT;
    if (rowTop > scoreArea.scrollTop + scoreArea.clientHeight - ROW_HEIGHT * 2) {
      scoreArea.scrollTo({ top: rowTop - 40, behavior: 'smooth' });
    }
  }
}

export function clearHighlight() {
  if (highlightRect) {
    highlightRect.setAttribute('width', '0');
    highlightRect.setAttribute('height', '0');
  }
}

// SVG helpers
function createText(content, x, y, fontSize, fill) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  el.setAttribute('x', x);
  el.setAttribute('y', y);
  el.setAttribute('font-size', fontSize);
  el.setAttribute('fill', fill);
  el.setAttribute('font-family', '-apple-system, sans-serif');
  el.textContent = content;
  return el;
}

function createLine(x1, y1, x2, y2, stroke, width = 1) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', 'line');
  el.setAttribute('x1', x1);
  el.setAttribute('y1', y1);
  el.setAttribute('x2', x2);
  el.setAttribute('y2', y2);
  el.setAttribute('stroke', stroke);
  el.setAttribute('stroke-width', width);
  return el;
}

function createCircle(cx, cy, r, fill) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  el.setAttribute('cx', cx);
  el.setAttribute('cy', cy);
  el.setAttribute('r', r);
  el.setAttribute('fill', fill);
  return el;
}
```

**Step 2: Test with fixture data in browser**

Temporarily update `src/main.js` to load the test fixture and render:
```js
import { parseMusicXML } from './parser.js';
import { renderJianpu } from './jianpu.js';

// For testing: load fixture directly
fetch('/test/fixtures/twinkle.musicxml')
  .then(r => r.text())
  .then(xml => {
    const data = parseMusicXML(xml);
    const svg = document.getElementById('jianpu-svg');
    document.getElementById('empty-state').style.display = 'none';
    renderJianpu(svg, data);
  });
```

```bash
npx vite
```
Expected: Browser shows "1=C 4/4" header and "1 1 5 5 | 6 6 5 − | 4 4 3 3 | 2 2 1 −" in jianpu notation.

**Step 3: Commit**

```bash
git add src/jianpu.js
git commit -m "feat: jianpu SVG renderer with highlight support"
```

---

### Task 5: Wire Everything Together (main.js)

**Files:**
- Modify: `src/main.js`

**Step 1: Implement full main.js**

Write `src/main.js`:
```js
import { parseMusicXML } from './parser.js';
import { renderJianpu, highlightNote, clearHighlight } from './jianpu.js';
import { initAudio, scheduleNotes, setupMetronome, setBpm, play, pause, stop, seekToBeat, setMetronomeEnabled, setVolume, getTransportState, getTotalBeats } from './audio.js';
import './style.css';

let scoreData = null;
let audioReady = false;
let isPlaying = false;

// DOM elements
const fileInput = document.getElementById('file-input');
const btnPlay = document.getElementById('btn-play');
const btnRestart = document.getElementById('btn-restart');
const bpmSlider = document.getElementById('bpm-slider');
const bpmValue = document.getElementById('bpm-value');
const bpmDisplay = document.getElementById('bpm-display');
const btnSlower = document.getElementById('btn-slower');
const btnFaster = document.getElementById('btn-faster');
const metroToggle = document.getElementById('metro-toggle');
const volumeSlider = document.getElementById('volume');
const keySig = document.getElementById('key-sig');
const timeSig = document.getElementById('time-sig');
const emptyState = document.getElementById('empty-state');
const svg = document.getElementById('jianpu-svg');
const progress = document.getElementById('progress');
const timeDisplay = document.getElementById('time-display');

// File upload
fileInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => loadScore(reader.result);
  reader.readAsText(file);
});

// Drag & drop on score area
const scoreArea = document.getElementById('score-area');
scoreArea.addEventListener('dragover', (e) => { e.preventDefault(); scoreArea.style.background = '#f0f4ff'; });
scoreArea.addEventListener('dragleave', () => { scoreArea.style.background = ''; });
scoreArea.addEventListener('drop', (e) => {
  e.preventDefault();
  scoreArea.style.background = '';
  const file = e.dataTransfer.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = () => loadScore(reader.result);
    reader.readAsText(file);
  }
});

function loadScore(xmlString) {
  scoreData = parseMusicXML(xmlString);
  emptyState.style.display = 'none';

  // Update header
  keySig.textContent = `1=${scoreData.key}`;
  timeSig.textContent = `${scoreData.timeBeats}/${scoreData.timeBeatType}`;
  updateBpmDisplay(scoreData.tempo);
  bpmSlider.value = scoreData.tempo;

  // Render jianpu
  renderJianpu(svg, scoreData);

  // Reset playback
  if (isPlaying) { stop(); isPlaying = false; btnPlay.textContent = '▶'; }
  clearHighlight();
}

async function ensureAudio() {
  if (!audioReady) {
    await initAudio();
    audioReady = true;
  }
}

// Play / Pause
btnPlay.addEventListener('click', async () => {
  if (!scoreData) return;
  await ensureAudio();

  if (isPlaying) {
    pause();
    isPlaying = false;
    btnPlay.textContent = '▶';
  } else {
    setBpm(parseInt(bpmSlider.value));
    setupMetronome(scoreData.timeBeats);
    scheduleNotes(scoreData.notes, (noteIndex) => {
      highlightNote(noteIndex);
      updateProgress(noteIndex);
      // Auto-stop at end
      if (noteIndex === scoreData.notes.length - 1) {
        setTimeout(() => {
          stop();
          isPlaying = false;
          btnPlay.textContent = '▶';
          clearHighlight();
        }, 2000);
      }
    });
    play();
    isPlaying = true;
    btnPlay.textContent = '⏸';
  }
});

// Restart
btnRestart.addEventListener('click', () => {
  if (!scoreData) return;
  stop();
  isPlaying = false;
  btnPlay.textContent = '▶';
  clearHighlight();
  progress.value = 0;
  timeDisplay.textContent = '0:00';
});

// BPM controls
function updateBpmDisplay(bpm) {
  bpmValue.textContent = `♩=${bpm}`;
  bpmDisplay.textContent = `♩=${bpm}`;
}

bpmSlider.addEventListener('input', () => {
  const bpm = parseInt(bpmSlider.value);
  updateBpmDisplay(bpm);
  setBpm(bpm);
});

btnSlower.addEventListener('click', () => {
  const bpm = Math.max(20, parseInt(bpmSlider.value) - 5);
  bpmSlider.value = bpm;
  updateBpmDisplay(bpm);
  setBpm(bpm);
});

btnFaster.addEventListener('click', () => {
  const bpm = Math.min(200, parseInt(bpmSlider.value) + 5);
  bpmSlider.value = bpm;
  updateBpmDisplay(bpm);
  setBpm(bpm);
});

// Metronome toggle
metroToggle.addEventListener('change', () => {
  setMetronomeEnabled(metroToggle.checked);
});

// Volume
volumeSlider.addEventListener('input', () => {
  const val = parseInt(volumeSlider.value);
  // Map 0-100 to -30dB...0dB
  const db = val === 0 ? -Infinity : -30 + (val / 100) * 30;
  setVolume(db);
});

// Progress tracking
function updateProgress(noteIndex) {
  if (!scoreData) return;
  const totalBeats = getTotalBeats(scoreData.notes);
  const currentBeat = scoreData.notes[noteIndex].beat;
  progress.value = (currentBeat / totalBeats) * 100;

  // Time display
  const bpm = parseInt(bpmSlider.value);
  const elapsed = (currentBeat / bpm) * 60;
  const min = Math.floor(elapsed / 60);
  const sec = Math.floor(elapsed % 60);
  timeDisplay.textContent = `${min}:${String(sec).padStart(2, '0')}`;
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  if (e.code === 'Space') {
    e.preventDefault();
    btnPlay.click();
  }
});
```

**Step 2: Test full flow in browser**

```bash
npx vite
```
Expected:
1. Upload twinkle.musicxml -> jianpu renders with "1 1 5 5 | 6 6 5 − | ..."
2. Click play -> piano plays Twinkle Twinkle with metronome, notes highlight in sync
3. BPM slider changes tempo in real-time
4. Metronome toggle works
5. Space bar toggles play/pause
6. Restart button resets to beginning

**Step 3: Commit**

```bash
git add src/main.js
git commit -m "feat: wire all modules - complete sight-singing player"
```

---

### Task 6: Polish & Deploy

**Files:**
- Modify: `src/style.css` (responsive tweaks)
- Modify: `index.html` (meta tags)

**Step 1: Add responsive styles and loading state**

Append to `src/style.css`:
```css
/* Loading indicator */
#loading {
  display: none;
  text-align: center;
  padding: 12px;
  color: #666;
  font-size: 14px;
}
#loading.visible { display: block; }

/* Responsive */
@media (max-width: 600px) {
  #info-bar { font-size: 13px; gap: 8px; }
  #controls { font-size: 13px; }
  #transport-row button, #speed-row button { width: 32px; height: 32px; }
}

/* Active state for play button */
#btn-play.playing {
  background: #4a90d9;
  color: white;
  border-color: #4a90d9;
}

/* Drag-over visual feedback */
#score-area.drag-over {
  background: #f0f4ff !important;
  border: 2px dashed #4a90d9;
}
```

**Step 2: Build and verify**

```bash
npx vite build
npx vite preview
```
Expected: Production build works, all features functional.

**Step 3: Deploy to Vercel**

Use the `deploy` skill to deploy `inbox/sight-singing/dist` to Vercel.

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: sight-singing tool v1 - polish and deploy"
```
