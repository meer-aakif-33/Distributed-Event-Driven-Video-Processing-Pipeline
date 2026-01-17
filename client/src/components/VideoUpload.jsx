import React, { useState } from "react";
import { Upload, Loader, AlertCircle } from "lucide-react";

const VideoUpload = ({ onUpload, isLoading }) => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      validateAndSetFile(selectedFile);
    }
  };

  const validateAndSetFile = (selectedFile) => {
    const MAX_SIZE = 500 * 1024 * 1024; // 500MB
    const validTypes = ['video/mp4', 'video/webm', 'video/x-msvideo', 'video/quicktime'];

    if (selectedFile.size > MAX_SIZE) {
      setError("File size must be less than 500MB");
      setFile(null);
      return;
    }

    if (!validTypes.includes(selectedFile.type)) {
      setError("Unsupported video format. Please use MP4, WebM, AVI, or MOV");
      setFile(null);
      return;
    }

    setError(null);
    setFile(selectedFile);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (file && !isLoading) {
      setLoading(true);
      try {
        await onUpload(file);
        setFile(null);
      } catch (err) {
        console.error("Upload error:", err);
      } finally {
        setLoading(false);
      }
    }
  };

  const getFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes, k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center px-4 py-8">
      <form
        onSubmit={handleSubmit}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`w-full max-w-xl transition-all duration-300 ${
          dragActive ? "scale-105" : ""
        }`}
      >
        <div className="bg-white/10 backdrop-blur-2xl rounded-2xl shadow-2xl border border-white/20 p-8 space-y-6">
          {/* Header */}
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-full mb-4">
              <Upload className="text-white" size={32} />
            </div>
            <h2 className="text-4xl font-bold bg-gradient-to-r from-cyan-300 to-blue-400 bg-clip-text text-transparent mb-2">
              Video Enhancement
            </h2>
            <p className="text-gray-300 text-sm">
              Upload your video for AI-powered enhancement and processing
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-lg flex gap-3">
              <AlertCircle className="text-red-400 flex-shrink-0 mt-0.5" size={20} />
              <p className="text-red-300 text-sm">{error}</p>
            </div>
          )}

          {/* Drop Zone */}
          <div
            className={`relative border-2 border-dashed rounded-xl p-8 transition-all ${
              dragActive
                ? "border-cyan-400 bg-cyan-400/10"
                : "border-gray-400 hover:border-cyan-400 bg-white/5 hover:bg-cyan-400/5"
            }`}
          >
            <input
              type="file"
              onChange={handleChange}
              accept="video/*"
              disabled={loading || isLoading}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
            />

            <div className="text-center pointer-events-none">
              {file ? (
                <div className="space-y-2">
                  <div className="text-3xl">🎬</div>
                  <p className="text-white font-semibold">{file.name}</p>
                  <p className="text-gray-300 text-sm">
                    {getFileSize(file.size)}
                  </p>
                  <p className="text-cyan-400 text-xs mt-2">✓ Ready to upload</p>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="text-4xl">📹</div>
                  <p className="text-white font-semibold">
                    Drag and drop your video here
                  </p>
                  <p className="text-gray-400 text-sm">or click to browse files</p>
                  <p className="text-gray-500 text-xs mt-3">
                    MP4, WebM, AVI, MOV • Max 500MB
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !file || isLoading}
            className={`w-full py-4 px-6 text-lg font-bold rounded-xl transition-all duration-200 shadow-lg flex items-center justify-center gap-2 ${
              loading || !file || isLoading
                ? "bg-gray-600 cursor-not-allowed text-gray-400"
                : "bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white hover:shadow-xl transform hover:scale-105"
            }`}
          >
            {loading || isLoading ? (
              <>
                <Loader className="animate-spin" size={20} />
                <span>Processing your video...</span>
              </>
            ) : (
              <>
                <Upload size={20} />
                <span>Process Video</span>
              </>
            )}
          </button>

          {/* Info Footer */}
          <div className="space-y-2 text-center">
            <p className="text-gray-400 text-xs">
              ✨ Your video will be enhanced with brightness and contrast optimization
            </p>
            <p className="text-gray-500 text-xs">
              🔒 Your files are processed securely and stored temporarily
            </p>
          </div>
        </div>
      </form>
    </div>
  );
};

export default VideoUpload;
