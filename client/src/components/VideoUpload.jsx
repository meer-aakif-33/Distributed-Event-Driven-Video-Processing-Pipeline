import React, { useState } from "react";

const VideoUpload = ({ onUpload }) => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false); // Spinner state

  const handleChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (file) {
      setLoading(true);
      await onUpload(file);   // Wait for upload to complete
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-pink-100 to-yellow-100 flex items-center justify-center px-4 py-8 ">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md bg-white/80 backdrop-blur-md p-8 rounded-2xl shadow-xl space-y-6 border border-white/30"
      >
        <h2 className="text-3xl font-bold text-center text-gray-800 mb-4">
          🎥 Upload Your Video
        </h2>

        <input
          type="file"
          onChange={handleChange}
          accept="video/*"
          disabled={loading}
          className="w-full cursor-pointer text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-100 file:text-indigo-700 hover:file:bg-indigo-200 transition cursor:pointer"
        />

        <button
          type="submit"
          disabled={loading}
          className={`w-full py-3 px-4 text-lg font-medium rounded-xl transition duration-200 shadow-md ${
            loading
              ? "bg-indigo-300 cursor-not-allowed"
              : "bg-indigo-600 hover:bg-indigo-700 text-white "
          }`}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg
                className="animate-spin h-5 w-5 text-white"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v8z"
                />
              </svg>
              Uploading...
            </span>
          ) : (
            "Upload"
          )}
        </button>
      </form>
    </div>
  );
};

export default VideoUpload;
