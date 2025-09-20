#!/usr/bin/env python3
# Fetch a full Street View pano via the official Map Tiles API and stitch it.
# minimal deps: requests, Pillow

import os, re, io, math, json, urllib.parse as up
import requests
from PIL import Image

URL = "https://www.google.com/maps/@33.9922558,-118.4029686,3a,75y,148.67h,98.01t/data=!3m7!1e1!3m5!1sGJ99KitLZxEpsY4Yx9PV2g!2e0!6shttps:%2F%2Fstreetviewpixels-pa.googleapis.com%2Fv1%2Fthumbnail%3Fcb_client%3Dmaps_sv.tactile%26w%3D900%26h%3D600%26pitch%3D-8.009855159718882%26panoid%3DGJ99KitLZxEpsY4Yx9PV2g%26yaw%3D148.67420935522165!7i16384!8i8192?entry=ttu"
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def extract_from_maps_url(url: str):
    # pull yaw/pitch/panoid from the embedded thumbnail qs
    parsed = up.urlparse(url)
    haystack = (parsed.path or "") + "?" + (parsed.query or "")
    m = re.search(r"https:%2F%2Fstreetviewpixels.*?%3F([^!]+)", haystack)
    if not m:
        # fallback: try the "!1s<id>" token right after 3m5
        m2 = re.search(r"!3m5!1s([^!]+)", haystack)
        pano = m2.group(1) if m2 else None
        return pano, None, None
    qs = up.parse_qs(m.group(1).replace("%26","&").replace("%3D","="))
    pano = (qs.get("panoid") or [None])[0]
    yaw = float((qs.get("yaw") or ["0"])[0])
    pitch = float((qs.get("pitch") or ["0"])[0])
    return pano, yaw, pitch

def create_session():
    # required for tiles; set mapType=streetview
    r = requests.post(
        "https://tile.googleapis.com/v1/createSession",
        params={"key": API_KEY},
        json={"mapType": "streetview", "language": "en-US", "region": "US"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["session"]

def get_metadata(session, pano_id=None, lat=None, lng=None, radius=50):
    # metadata gives image/tile sizes and copyright
    params = {"session": session, "key": API_KEY}
    if pano_id:
        params["panoId"] = pano_id
    else:
        params.update({"lat": lat, "lng": lng, "radius": radius})
    r = requests.get("https://tile.googleapis.com/v1/streetview/metadata", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def fetch_tile(session, pano_id, z, x, y):
    params = {"session": session, "key": API_KEY, "panoId": pano_id}
    url = f"https://tile.googleapis.com/v1/streetview/tiles/{z}/{x}/{y}"
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGB")

def stitch_pano(meta, session, pano_id, z=5):
    # compute tile grid from metadata
    tw, th = meta["tileWidth"], meta["tileHeight"]
    W, H = meta["imageWidth"], meta["imageHeight"]
    # at z=5 you’re at native resolution
    tiles_x = math.ceil(W / tw)
    tiles_y = math.ceil(H / th)
    canvas = Image.new("RGB", (tiles_x * tw, tiles_y * th))
    for y in range(tiles_y):
        for x in range(tiles_x):
            tile = fetch_tile(session, pano_id, z, x, y)
            canvas.paste(tile, (x * tw, y * th))
    # crop to exact pano dims
    return canvas.crop((0, 0, W, H))

def write_xmp_360(path, img):
    # tiny XMP to flag as equirectangular 360 (PhotoSphere)
    # ref: GPano schema. minimal fields.
    xmp = (
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        '<rdf:Description xmlns:GPano="http://ns.google.com/photos/1.0/panorama/" '
        'GPano:ProjectionType="equirectangular" '
        f'GPano:FullPanoWidthPixels="{img.width}" '
        f'GPano:FullPanoHeightPixels="{img.height}" '
        'GPano:CroppedAreaLeftPixels="0" GPano:CroppedAreaTopPixels="0" '
        f'GPano:CroppedAreaImageWidthPixels="{img.width}" '
        f'GPano:CroppedAreaImageHeightPixels="{img.height}" />'
        '</rdf:RDF></x:xmpmeta>'
    ).encode("utf-8")
    # embed as APP1 after EXIF (Pillow trick: save, then append XMP)
    img.save(path, format="JPEG", quality=92)
    with open(path, "rb+") as f:
        data = f.read()
        insert_at = data.find(b"http://ns.adobe.com/xap/1.0/\x00")
        if insert_at == -1:
            # naive append as a separate APP1, good enough for local use
            f.seek(0, 2)
            f.write(b"\xff\xe1" + len(xmp + b"http://ns.adobe.com/xap/1.0/\x00" + b"\x00").to_bytes(2, "big"))
            f.write(b"http://ns.adobe.com/xap/1.0/\x00")
            f.write(xmp)

def main():
    if not API_KEY:
        raise SystemExit("Set GOOGLE_MAPS_API_KEY")
    pano, yaw, pitch = extract_from_maps_url(URL)
    session = create_session()
    meta = get_metadata(session, pano_id=pano)
    pano_img = stitch_pano(meta, session, pano_id=meta["panoId"], z=5)
    out = f"streetview_{meta['panoId']}_{meta['imageWidth']}x{meta['imageHeight']}.jpg"
    write_xmp_360(out, pano_img)
    print(f"saved {out}  | date={meta.get('date')}  | copyright={meta.get('copyright')}")

if __name__ == "__main__":
    main()
