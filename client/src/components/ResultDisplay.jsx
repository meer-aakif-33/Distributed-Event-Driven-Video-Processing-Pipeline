import React, { useEffect, useRef, useState } from "react";
import { Play, Download, X, Copy, Check } from "lucide-react";

const ResultDisplay = ({ metadata, videoUrl }) => {
  const resultRef = useRef(null);
  const [showMetadata, setShowMetadata] = useState(false);
  const [copied, setCopied] = useState(false);
  const [videoTime, setVideoTime] = useState("0:00");
  const [videoDuration, setVideoDuration] = useState("0:00");
  const videoRef = useRef(null);

  useEffect(() => {
    console.log("[] Props updated in ResultDisplay:");
    console.log("Metadata:", metadata);
    console.log("Video URL:", videoUrl);

    if (metadata && videoUrl && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [metadata, videoUrl]);

  const handleCopyUrl = () => {
    if (videoUrl) {
      navigator.clipboard.writeText(videoUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleTimeUpdate = (e) => {
    const video = e.target;
    const current = formatTime(video.currentTime);
    const duration = formatTime(video.duration);
    setVideoTime(current);
    setVideoDuration(duration);
  };

  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const getFilename = (url) => {
    if (!url) return null;
    const parts = url.split("/");
    const raw = parts[parts.length - 1];
    return raw.split("?")[0];
  };

  const filename = getFilename(videoUrl);
  const downloadUrl = filename ? `http://localhost:8000/download/${filename}` : null;
  const playableUrl = videoUrl;

  const formatMetadata = (data) => {
    if (!data) return {};
    const formatted = {};
    Object.keys(data).forEach(key => {
      const value = data[key];
      if (typeof value === "object") {
        formatted[key] = JSON.stringify(value, null, 2);
      } else {
        formatted[key] = value;
      }
    });
    return formatted;
  };

  const metadataEntries = metadata ? {
    ...formatMetadata(metadata.enhancement),
    ...formatMetadata(metadata.metadata_extraction)
  } : {};

  return (
    <>
      {metadata && videoUrl && (
        <div
          ref={resultRef}
          className="mt-12 w-full max-w-6xl mx-auto px-4"
        >
          {/* Success Banner */}
          <div className="mb-6 bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/50 rounded-xl p-6 shadow-lg backdrop-blur">
            <div className="flex items-center gap-3">
              <div className="text-3xl">✅</div>
              <div>
                <h2 className="text-2xl font-bold text-green-300">Processing Complete!</h2>
                <p className="text-green-200/80 text-sm mt-1">Your enhanced video is ready for preview or download</p>
              </div>
            </div>
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Video Player - Takes 3 columns on large screens */}
            <div className="lg:col-span-3">
              <div className="bg-white/10 backdrop-blur-2xl rounded-xl shadow-2xl overflow-hidden border border-white/20">
                <div className="aspect-video bg-black relative group">
                  <video
                    ref={videoRef}
                    key={videoUrl}
                    controls
                    onTimeUpdate={handleTimeUpdate}
                    onLoadedMetadata={(e) => {
                      setVideoDuration(formatTime(e.target.duration));
                    }}
                    className="w-full h-full"
                    controlsList="nodownload"
                    style={{
                      filter: "drop-shadow(0 0 20px rgba(34, 197, 94, 0.3))"
                    }}
                  >
                    <source src={playableUrl} type="video/mp4" />
                    Your browser does not support the video tag.
                  </video>
                </div>

                {/* Video Info & Action Buttons */}
                <div className="p-4 bg-gradient-to-b from-white/10 to-white/5 border-t border-white/10 space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-300">Duration: {videoDuration}</span>
                  </div>

                  <div className="flex gap-2 flex-wrap">
                    {downloadUrl && (
                      <a
                        href={downloadUrl}
                        download
                        className="flex-1 min-w-[160px] flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white font-semibold rounded-lg transition shadow-lg hover:shadow-xl"
                      >
                        <Download size={18} />
                        <span>Download</span>
                      </a>
                    )}

                    <button
                      onClick={handleCopyUrl}
                      className="flex items-center justify-center gap-2 px-4 py-3 bg-white/10 hover:bg-white/20 text-white rounded-lg transition border border-white/20"
                    >
                      {copied ? (
                        <Check size={18} className="text-green-400" />
                      ) : (
                        <Copy size={18} />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Metadata Sidebar */}
            <div className="lg:col-span-1">
              <div className="bg-white/10 backdrop-blur-2xl rounded-xl shadow-2xl border border-white/20 overflow-hidden sticky top-4">
                <button
                  onClick={() => setShowMetadata(!showMetadata)}
                  className="w-full px-4 py-4 bg-gradient-to-r from-purple-500/30 to-pink-500/30 hover:from-purple-500/40 hover:to-pink-500/40 border-b border-white/10 flex items-center justify-between transition"
                >
                  <h3 className="font-bold text-white">Video Info</h3>
                  <span className={`text-cyan-400 transform transition ${showMetadata ? 'rotate-180' : ''}`}>
                    ▼
                  </span>
                </button>

                {showMetadata && (
                  <div className="p-4 max-h-[600px] overflow-y-auto space-y-3">
                    {Object.entries(metadataEntries).length > 0 ? (
                      Object.entries(metadataEntries).map(([key, value]) => (
                        <div key={key} className="border-l-4 border-cyan-400 pl-3 py-2">
                          <p className="text-xs font-bold text-cyan-300 uppercase tracking-widest">
                            {key.replace(/_/g, " ")}
                          </p>
                          <p className="text-sm text-gray-200 mt-1 break-words font-mono text-xs bg-white/5 p-2 rounded border border-white/10">
                            {typeof value === 'string' ? value : JSON.stringify(value)}
                          </p>
                        </div>
                      ))
                    ) : (
                      <p className="text-gray-400 text-sm text-center py-4">
                        No metadata available
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ResultDisplay;
