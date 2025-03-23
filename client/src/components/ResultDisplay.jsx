import React, { useEffect } from "react";

const ResultDisplay = ({ metadata, videoUrl }) => {
  useEffect(() => {
    console.log("[🔄] Props updated in ResultDisplay:");
    console.log("Metadata:", metadata);
    console.log("Video URL:", videoUrl);
  }, [metadata, videoUrl]);


  return (
    <div className="mt-10 w-full max-w-2xl mx-auto bg-white p-6 rounded-2xl shadow-lg border border-gray-200">
      <h2 className="text-2xl font-bold text-center text-green-600 mb-6">
        ✅ Processing Complete
      </h2>

      {metadata && (
        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-700 mb-2">Metadata:</h3>
          <pre className="bg-gray-100 p-4 rounded-lg text-sm overflow-x-auto whitespace-pre-wrap">
            {JSON.stringify(metadata, null, 2)}
          </pre>
        </div>
      )}

      {videoUrl && (
        <div>
          <h3 className="text-lg font-medium text-gray-700 mb-2">Enhanced Video:</h3>
          <div className="rounded-lg overflow-hidden shadow-sm">
            <video
              controls
              className="w-full rounded-md border border-gray-300"
            >
              <source src={videoUrl} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </div>
        </div>
      )}

      {videoUrl && (
        <a
          href={videoUrl}
          download
          className="inline-block mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
        >
          Download Enhanced Video
        </a>
      )}
    </div>
  );
};

export default ResultDisplay;
