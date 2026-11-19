# AI dataset research — candidate, not downloaded

Checked **2026-11-19**. This is a research shortlist only. No dataset has been downloaded, unpacked, or used for training. Keep all six product categories. The provisional candidate model covers `pothole`, `garbage`, and `water_leakage`; the other product categories show **no suggestion** until an image dataset with clear rights and a usable held-out group split is found. No claim about model quality is made.

## Category candidates

| Product category | Candidate and source | Licence | Size and labels | Problems and decision |
|---|---|---|---|---|
| `pothole` | [Attain](https://data.mendeley.com/datasets/nykrzdm74f/1) | CC BY 4.0 stated on Mendeley Data. | 2,293 images; 19,761 distress instances; 10 pavement-distress types including potholes; object annotations. Archive byte size is not shown in the record. | Vehicle-windshield images from pavement drives can contain correlated frames. The public record does not document a source/route split, so inspect identifiers and near-duplicates before splitting. It is a candidate, not yet proven to support single-label complaint categorization. |
| `garbage` | [TACO — Trash Annotations in Context](https://github.com/pedropro/TACO) | Image rights are per source image; use only image records whose annotation metadata gives an explicit compatible licence (for example CC BY or CC0). The repository's MIT licence covers toolkit code, not automatically the photos. | About 1,500 images and 4,784 litter instances in the dataset paper; 60 litter labels grouped into 28 super-categories; instance masks and scene tags. Exact archive size is not published on the official source page. | Rights vary by image; an image without a clear compatible grant is excluded. Many fine-grained labels are sparse, crowdsourced, and not equivalent to a municipal garbage complaint. Images are mostly positive for litter, so there is no natural clean-street negative class. Check duplicated scenes/source URLs and use source/scene groups. |
| `drainage` | [Culvert Visual Blockage Assessment Dataset](https://zenodo.org/records/7623641) | Zenodo record has no dataset licence value. | 3.3 GB; synthetic SIC plus lab VHD images; debris/blockage conditions include urban, vegetative, and mixed. | No explicit dataset licence: do not use until rights are stated. Synthetic and scale-model imagery has a substantial gap from a citizen photo of a blocked street drain. Repeated simulation/experiment frames need group-held-out splitting. **Not eligible now.** |
| `streetlight` | [Images of Public Streetlights with Operational Monitoring](https://zenodo.org/records/6046759) | Zenodo record's Rights/License field is blank. The associated article's CC BY notice is not treated as a licence for the image archive. | About 350,000 JPEGs; 158.2 GB complete files, 1.0 GB example package; labels are lamp `ON`/`OFF`. | Dataset rights are unclear until the image archive itself gets a licence. `ON`/`OFF` is not the same as a reported broken light. Repeated hourly photos of the same pole are highly correlated; split by pole/node, never image. **Not eligible now.** |
| `water_leakage` | [Water leakage images](https://data.mendeley.com/datasets/xz2nykszbs/1) | CC BY 4.0 stated on Mendeley Data. | Image archive and training/validation label files are listed; one category, `Leakage`. Record does not give image count or archive byte size. | Verify exact image provenance, scene grouping, label schema, and permissions before use; the contributor metadata is sparse and no held-out test split is supplied. Interior/structural leakage photos may not match municipal water-main leaks. Candidate only after a source/group split can be built. |
| `other` | No candidate selected. | — | “Other” is an open-ended catch-all rather than a stable visual class. | Do not train an `other` output. It should receive no suggestion; the reviewer retains the manual category choice. |

### Additional findings

- [RDD2022](https://doi.org/10.1002/gdj3.260) is a strong pothole benchmark candidate: 47,420 road images from six countries, with 55,000+ instances in four damage labels (D00, D10, D20, D40/pothole). Its Figshare catalogue record identifies CC BY 4.0, while the official RoadDamageDetector project describes images as CC BY-SA 4.0. Treat that conflict as unresolved and do not use RDD2022 until the exact release asset's licence is reconciled. The official challenge page lists country archives from about 245 MB to 9.9 GB.
- [Rubbish Open Data](https://www.rubbish.love/open-data) declares CC BY 4.0 for 212,859 photo records, but its downloadable tables explicitly contain no photos or photo links. It cannot be used to train the image classifier.
- [Sewer-ML](https://vap.aau.dk/sewer-ml/) contains 1,300,201 pipe-inspection frames from 75,618 videos and 17 inspector-coded sewer defect classes, but its project page does not state a dataset licence. It is also internal sewer imagery rather than street-drain reports. Do not use unless the rights and category mapping are resolved.
- [PavementDamagesG-7](https://data.mendeley.com/datasets/yb65trwbd8/1) is a smaller CC BY 4.0 candidate with a 208 MB archive, road-surface masks for potholes and drain features, and repeated capture along road segments. “Drain” presence is not necessarily a drainage failure, so do not count it as a confirmed `drainage` class.

## Provisional recommendation

If a later rights and split audit passes, trial exactly three outputs: `pothole` (Attain), `garbage` (only individually cleared TACO images), and `water_leakage` (Mendeley image set). This is provisional rather than a finding that all three are ready: the garbage subset size and water-leakage grouping are unknown today. Do not fill a fourth class merely to reach a target. The product retains six categories; unsupported categories show no suggestion. If fewer than three categories survive the rights/split audit, keep the slice limited to categories that pass and show no suggestion for the rest; do not broaden licences or infer a result. Drop the slice only if no category has a usable, clearly licensed dataset.

## Proposed free-notebook training plan

Use a Google Colab free notebook as a convenience, not a guaranteed resource: Google says free runtimes can run at most 12 hours depending on availability and usage, and GPU availability/limits vary. Save a small checkpoint and split manifest outside the ephemeral runtime after each stage; do not put unlicensed data or credentials in a shared notebook.

1. Before any download, preserve the dataset version/DOI, licence text, required attribution, and source file manifest. Download only the specific licensed candidates later approved; record file hashes and image-level rights for TACO. Do not include personally identifying image metadata in exported manifests.
2. Build a one-image/one-target subset only from clearly mapped examples. For object or segmentation annotations, mark a report category present only where the source annotation supports that label; do not infer “no problem” from an absent annotation.
3. Find source groups before splitting: video/drive route, pole, collection session, or original image URL/scene. Group exact and perceptual-hash near-duplicates together. Use a deterministic group-based train/validation/test split (rough target 70/15/15); if group IDs are missing or too few, stop and document that dataset as unusable for this evaluation rather than random-splitting images.
4. Start with pretrained torchvision MobileNetV3-Small, replace the final classifier for the supported class count, use 224x224 RGB inputs and the pretrained weights' documented normalization, and fine-tune with early stopping on validation macro-F1. Do not choose thresholds after looking at test results.
5. Record exact sample counts and group counts by split and class, class imbalance, per-class precision/recall/F1/support, macro-F1, confusion matrix, overall accuracy, the fixed low-confidence threshold, seed, training config, model/weight source and licence, and failure cases. The report must present measured values, not targets.
6. Keep one untouched group-held-out test set for the only final evaluation. Compare a simple majority-class baseline. Check errors by dataset/source, lighting, and capture condition because source-specific cues can masquerade as complaint-category accuracy.

### Required export artifacts

The notebook must produce and validate all of these before an inference implementation is attempted:

- `ml/models/category_classifier.onnx` — ONNX graph with fixed RGB preprocessing contract and named input/output tensors.
- `ml/models/labels.json` — ordered list of supported category names and preprocessing metadata; never include unsupported categories.
- `ml/metrics/evaluation.json` — data source/version/licence references, split group/sample counts, seed/config, per-class metrics, aggregate metrics, threshold and test-set results.
- `ml/metrics/confusion_matrix.png` — labelled held-out-test confusion matrix with supports.
- `ml/THRESHOLDS.md` — threshold selection procedure and frozen threshold, written before test-set evaluation.
- `ml/DATASETS.md` — final dataset provenance, licences, exclusions, and group-split method.

Verify the current PyTorch ONNX exporter and ONNX Runtime APIs before dependency pinning or implementation. Prefer `torch.onnx.export(..., dynamo=True, verify=True)` when supported by the selected notebook versions, then load the artifact in `onnxruntime` with `CPUExecutionProvider` and compare its logits on a fixed validation batch against PyTorch within a documented tolerance.

## Safe inference behavior (design only; not implemented)

`apps/ai_assist/classifier.py` should read an explicit `AI_MODEL_PATH` from the environment, lazily load the ONNX Runtime session and `labels.json`, and validate model input/output names, shapes, and label count once. If either file is missing, unreadable, or incompatible, the classifier is unavailable and returns no suggestion; the AI worker should mark any pending suggestion `failed` with a generic internal reason and continue. Complaint submission must not wait for or call inference, and no model output may set category, route, status, or priority automatically.
