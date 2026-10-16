from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import yt_dlp
import os

app = FastAPI()

# Enable CORS so HopWeb can talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def format_duration(seconds):
    if not seconds:
        return "Unknown"
    mins, secs = divmod(int(seconds), 60)
    return f"{mins}:{secs:02d}"

@app.get("/")
def serve_ui():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "Place index.html in the same directory"}

@app.get("/api/search")
def search_songs(q: str):
    if not q:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'skip_download': True,
        # FIXED: Added Android spoofing to bypass search blocks
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch8:{q}", download=False)
            entries = results.get('entries', [])

        tracks = []
        for e in entries:
            tracks.append({
                "id": e.get("id"),
                "title": e.get("title", "Unknown Title"),
                "uploader": e.get("uploader") or e.get("channel") or "Unknown Artist",
                "duration": format_duration(e.get("duration")),
                "thumbnail": f"https://i.ytimg.com/vi/{e.get('id')}/hqdefault.jpg"
            })
        return {"results": tracks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stream")
def get_stream(video_id: str):
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            stream_url = info.get("url")

            if not stream_url:
                raise HTTPException(status_code=404, detail="Stream URL not found")

            return {
                "id": video_id,
                "title": info.get("title"),
                "uploader": info.get("uploader"),
                "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                "stream_url": stream_url
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # FIXED: Removed reload=True to prevent Pydroid multiprocessing crashes
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
