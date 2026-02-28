# S3 CORS configuration for panel/image download

The frontend (mangakai.in) downloads panel and anime images by calling `fetch(presignedS3Url)`. Browsers block that cross-origin request unless the S3 bucket returns CORS headers.

**Symptom:** "Failed to load resource: net::ERR_FAILED" / "Download failed: TypeError: Failed to fetch" when clicking Download.

**Fix:** Add a CORS configuration to your S3 bucket (e.g. `mangakai-media-prod`).

## AWS Console

1. Open **S3** → your bucket (e.g. `mangakai-media-prod`) → **Permissions**.
2. Under **Cross-origin resource sharing (CORS)**, click **Edit**.
3. Paste the following (adjust origins if you use different domains):

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedOrigins": [
      "https://mangakai.in",
      "https://www.mangakai.in",
      "http://localhost:3000"
    ],
    "ExposeHeaders": []
  }
]
```

4. Save.

## AWS CLI

```bash
# Create a file cors.json with the content above, then:
aws s3api put-bucket-cors --bucket mangakai-media-prod --cors-configuration file://cors.json
```

After CORS is set, the Download button will work without opening a new tab. Until then, the frontend falls back to opening the image in a new tab so the user can right-click → Save image.
