# Learning Nurad: DICOM, Orthanc, OHIF, then AI

A 3-day path to go from "I don't know what DICOM is" to "I can read the OHIF/MONAI code in
this repo and experiment with it." Every exercise uses the actual running Nurad stack
(`./run.sh up`), not a generic tutorial elsewhere — you're practicing on real data already
loaded (a CT, a brain MRI, an X-ray, and an ultrasound study).

Budget ~2-3 focused hours/day. Read a little, then immediately do the hands-on part against
the running app — don't read all three days of theory before touching anything.

---

## Day 1 — DICOM & Orthanc (the data layer)

**Concepts to learn**
- The DICOM hierarchy: **Patient → Study → Series → Instance**. A "study" is one imaging
  encounter (e.g. one CT scan visit); a "series" is one acquisition within it (e.g. one MRI
  sequence); an "instance" is usually one image (or one frame-set for multi-frame like
  ultrasound).
- **Modality** codes: `CT`, `MR`, `US`, `CR`/`DX` (X-ray), `SEG` (segmentation), `SR`
  (structured report). You already have one of each except plain CR/DX loaded (yours is `RF`,
  radiofluoroscopy — same family).
- **DICOM tags**: every piece of metadata (PatientName, StudyDate, Modality, ...) is a numbered
  tag like `(0010,0010)`. You don't need to memorize tags, just recognize this is what
  "metadata" means in DICOM.
- **DICOMweb**: the HTTP/REST version of DICOM (QIDO-RS to search, WADO-RS to retrieve, STOW-RS
  to store) — this is what OHIF actually talks over the network, never the older
  TCP-socket DICOM protocol directly.
- **Orthanc**: the PACS (Picture Archiving and Communication System) in this stack — the actual
  server that stores DICOM files and serves both a native REST API and DICOMweb.

**Hands-on**
1. Open Orthanc's own UI: **http://localhost:8042** (basic auth from your `.env`). Browse the
   4 loaded studies. Click into one, look at "Study information" — this is the tag data from
   Day 1's first bullet, for real.
2. Try Orthanc's REST API directly:
   ```
   curl -u orthanc:<password> http://localhost:8042/studies
   curl -u orthanc:<password> http://localhost:8042/studies/<one-of-those-ids>
   ```
   Compare what you see to the Orthanc UI — same data, different shape.
3. Upload one more study yourself via Orthanc's "Upload" page (drag in a `.dcm` file) — if you
   don't have one handy, grab a small sample from https://www.rubomedical.com/dicom_files/
   (same source the 4 existing samples came from).
4. Read: [Orthanc Book — Introduction](https://orthanc.uclouvain.be/book/users/) (skim the
   first couple of pages, don't read the whole book) and
   [DICOM is Easy — a plain-English DICOM primer](https://dicomiseasy.blogspot.com/2011/10/introduction-to-dicom-chapter-1.html).

**You'll know Day 1 landed when**: you can look at a study in Orthanc's UI and correctly say
"this has N series, this one's the CT, that tag is the patient ID."

---

## Day 2 — OHIF: viewing and navigating

**Concepts to learn**
- OHIF is a **viewer** — it reads from a DICOMweb source (here, via the Django proxy in front
  of Orthanc) and renders it. It doesn't store anything itself.
- **Viewports**: the panels showing images. **Layout**: how many viewports, in what grid.
- **Window/Level**: how CT/MR pixel intensities map to grayscale — the single most important
  tool to understand, since "reading" any scan starts here.
- **MPR** (multiplanar reconstruction) / **Crosshairs**: viewing one 3D volume from 3
  orthogonal planes at once (axial/sagittal/coronal) instead of scrolling one stack.
- **Measurement tools**: Length, ROI (region of interest — circle/rectangle/freehand), Angle —
  these attach structured "measurements" to specific pixel locations, trackable across
  sessions.

**Hands-on** (log in at **http://localhost:3030**, `testuser`/`testpass123`)
1. Open the CT study. Practice: pan, zoom, scroll through slices (mouse wheel), adjust
   window/level (drag).
2. Try the **Layout** button — go to a 2x2 grid, put different series in different panes.
3. Open a study with more than one series (if you upload one) and try **Crosshairs**/MPR.
4. Try a couple of measurement tools — draw a Length line, an Elliptical ROI. Notice they
   persist and show up in a measurements panel.
5. Open the brain MRI. Notice how differently window/level behaves on MR vs CT (different
   intensity ranges/units — MR has no fixed scale like CT's Hounsfield units).
6. Read: [OHIF Viewer user docs — Basic Usage](https://docs.ohif.org/) (the "Viewer" section is
   what matters here; skip the developer/extension docs for now, that's Day 3).

**You'll know Day 2 landed when**: you can open any of the 4 loaded studies and confidently
window/level, scroll, and measure without hunting for buttons.

---

## Day 3 — Segmentation editing + just enough OHIF architecture

**Concepts to learn**
- **DICOM-SEG**: a segmentation mask stored as its own DICOM series, referencing the images it
  overlays. This is the output format the AI pipeline in this repo produces.
- **Labelmap vs. contour segmentation**: a labelmap paints pixels directly (brush/eraser); a
  contour traces an outline (freehand/spline/livewire) that gets filled in. Different editing
  feel, same underlying result.
- Just enough **OHIF architecture** to navigate this codebase:
  - **Extension**: a package providing tools/panels/viewports/commands (e.g.
    `extensions/cornerstone-dicom-seg`).
  - **Mode**: a named configuration that picks which extensions/tools/panels are active for a
    given workflow (e.g. `modes/longitudinal` — the "Basic Viewer" you've been using). Look at
    `viewer/modes/longitudinal/src/index.ts` after today's segmentation-editing change — you'll
    recognize the toolbar/tool-group concepts from what you just used in the browser.
  - **Toolbar button → command**: every button you click maps to a `commandName` registered
    somewhere in an extension. This is the thing to grep for when you want to know "what does
    this button actually do."

**Hands-on**
1. Open a study, find the segmentation panel (right side). If there's no segmentation loaded
   yet, run "AI Segmentation" on a CT study first (see the README) to get one.
2. Try the newly-enabled editing tools: **Brush**, **Eraser**, **Threshold** (labelmap), and
   **Freehand**/**Sculptor**/**Livewire** (contour). Paint on a slice, undo, adjust brush
   radius.
3. Export/store your edited segmentation (the "DICOM SEG" export option) and confirm in
   Orthanc's UI that a new SEG series shows up.
4. Skim `viewer/modes/longitudinal/src/initToolGroups.ts` and
   `viewer/modes/longitudinal/src/toolbarButtons.ts` in this repo — you now have the
   vocabulary to recognize what's happening in that config, even if the code style is still
   unfamiliar.

**You'll know Day 3 landed when**: you can create and edit a segmentation, understand *why* it
needed a code change to unlock that (editing was off by default), and can find the toolbar
button definition for any tool you clicked.

---

## After Day 3: starting the AI side

Once viewing/editing feels natural, move to the model side:

1. **Understand the existing pipeline first** (don't skip to building something new): read
   `monai-pipeline/segment.py` and `cluster/README.md`. Run "Run AI Segmentation" on the CT
   study end-to-end and watch the job status change (`Pending → Running → Succeeded`) — this is
   the whole current pipeline, MONAI Model Zoo bundle → Argo Workflow → DICOM-SEG back into
   Orthanc.
2. **MONAI basics**: skim the [MONAI Model Zoo](https://monai.io/model-zoo.html) — these are
   pretrained segmentation models you can drop in like the spleen one already wired up. Look at
   `wholeBrainSeg_Large_UNEST_segmentation` (133-structure whole-brain MRI) — this is the
   natural next model to try, matching your brain MRI sample study, per
   `.vscode/plan/01-ohif-capability-expansion.md`'s roadmap.
3. **First experiment**: once comfortable, try swapping the hardcoded `spleen_ct_segmentation`
   bundle reference in `backend/worklist/argo_client.py` for a second `WorkflowTemplate`
   pointing at a different model, following the exact pattern already in
   `cluster/workflow-template.yaml`. Small, contained, and teaches you the whole loop by
   changing one real piece of it.
4. **Longer-term direction to read up on**: [MONAI Label](https://docs.monai.io/projects/label/en/latest/)
   — interactive AI-assisted correction (DeepEdit) with a pre-built OHIF plugin. This is the
   more ambitious "AI-in-the-loop" direction flagged as a future spike, not something to start
   before the basics above feel solid.

Don't start the AI side by reading MONAI's own docs cold — you'll get much more out of it once
the DICOM-SEG / segmentation-editing concepts from Day 3 are concrete in your hands, since
that's the exact output format and review surface the AI side produces and depends on.
