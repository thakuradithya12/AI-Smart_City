# Owner photo intake

Only the owner-provided images are allowed for this first evaluation. Public datasets are not part of this run. Place the five supplied folders under `ml/data/`:

```text
ml/data/
├── manifest.csv
├── pothole/
├── garbage/
├── drainage/
├── streetlight/
└── other/
```

`manifest.csv` must have exactly two columns: `path,group_id`. Paths are relative to `ml/data/`, use forward slashes, and point to images in the category folders. `group_id` is an opaque label for a shared source scene, collection session, report, street segment, or pole. Images from the same scene/session and byte-identical copies must share a group. Do not place a person's name, email, exact address, phone number, or raw GPS coordinates in the manifest.

Supported image formats are JPEG, PNG, and WebP. The read-only preflight checks that bytes decode, extensions match image formats, image dimensions stay below 40 million pixels, manifest entries match the files, and byte-identical images are not assigned to different groups. Run it from the repository root:

```powershell
docker compose run --rm checks python ml/dataset_preflight.py
```

The `other` folder is retained for evaluating whether unsupported reports receive no suggestion; it is not a classifier output. Passing preflight only validates file and manifest structure. It does not prove that groups were assigned correctly, establish consent/licence, create train/validation/test splits, evaluate model quality, or authorize training. Do not train or claim metrics until those separate checks pass.

Photo data is ignored by Git and excluded from Docker build context. Keep the source folders local and do not include them in commits or images.
