import React, { useState, useEffect } from "react";
import axios from "axios";
import VideoUpload from "./components/VideoUpload";
import ResultDisplay from "./components/ResultDisplay";
import ProcessingStatus from "./components/ProcessingStatus";
import UploadHistory from "./components/UploadHistory";
import './App.css';

const App = () => {
  const [videoId, setVideoId] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [enhancedVideoUrl, setEnhancedVideoUrl] = useState(null);
  const [processingStatus, setProcessingStatus] = useState({
    uploading: false,
    processing: false,
    enhancement: false,
    metadata: false,
    progress: 0,
  });
  const [uploadHistory, setUploadHistory] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    console.log("App mounted.");
  }, []);

  const handleUpload = async (file) => {
    return new Promise(async (resolve, reject) => {
      try {
        console.log("Uploading file:", file.name);
        setError(null);
        setProcessingStatus(prev => ({
          ...prev,
          uploading: true,
          progress: 10,
        }));
  
        const formData = new FormData();
        formData.append("file", file);
  
        const res = await axios.post("http://localhost:8000/upload", formData, {
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 40) / progressEvent.total
            );
            setProcessingStatus(prev => ({
              ...prev,
              progress: 10 + percentCompleted,
            }));
          },
        });
        console.log("Upload response:", res.data);
  
        const { video_id } = res.data;
        setVideoId(video_id);
        setProcessingStatus(prev => ({
          ...prev,
          uploading: false,
          processing: true,
          progress: 50,
        }));
  
        // WebSocket connection that resolves when processing is done
        const ws = new WebSocket(`ws://localhost:8000/ws?video_id=${video_id}`);
  
        const wsTimeout = setTimeout(() => {
          ws.close();
          reject(new Error("Processing timeout - please try again"));
        }, 300000); // 5 minutes timeout
  
        ws.onopen = () => {
          console.log("WebSocket connected for:", video_id);
        };
  
        ws.onmessage = (event) => {
          console.log("Raw WebSocket message received:", event.data);
  
          try {
            const data = JSON.parse(event.data);
            console.log("Parsed WebSocket data:", data);
  
            if (data.message === "Processing complete!") {
              clearTimeout(wsTimeout);
              setMetadata(data.metadata);
              setEnhancedVideoUrl(data.enhanced_video_url);
              setProcessingStatus(prev => ({
                ...prev,
                processing: false,
                progress: 100,
                enhancement: true,
                metadata: true,
              }));
              
              // Add to history
              setUploadHistory(prev => [{
                id: video_id,
                filename: file.name,
                timestamp: new Date().toLocaleString(),
                videoUrl: data.enhanced_video_url,
                metadata: data.metadata,
              }, ...prev].slice(0, 10));
              
              ws.close();
              resolve();
            } else if (data.status) {
              // Update processing status
              setProcessingStatus(prev => ({
                ...prev,
                enhancement: data.status.enhancement || prev.enhancement,
                metadata: data.status.metadata || prev.metadata,
                progress: (data.status.enhancement && data.status.metadata) ? 100 : 75,
              }));
            }
          } catch (err) {
            console.error("Failed to parse WebSocket message:", err);
          }
        };
  
        ws.onerror = (e) => {
          console.error("WebSocket error:", e);
          clearTimeout(wsTimeout);
          setError("Connection error during processing");
          reject(e);
        };
  
        ws.onclose = () => {
          console.log("WebSocket connection closed.");
          clearTimeout(wsTimeout);
        };
      } catch (error) {
        console.error("Error uploading video:", error);
        setError(error.message || "Error uploading video");
        setProcessingStatus(prev => ({
          ...prev,
          uploading: false,
          processing: false,
        }));
        reject(error);
      }
    });
  };
  
return (
  <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
    <div className="py-8">
      {error && (
        <div className="max-w-4xl mx-auto px-4 mb-4 bg-red-500/20 border border-red-500/50 rounded-lg p-4">
          <p className="text-red-300">{error}</p>
          <button
            onClick={() => setError(null)}
            className="text-red-400 hover:text-red-300 text-sm mt-2"
          >
            Dismiss
          </button>
        </div>
      )}

      {(!metadata || !enhancedVideoUrl) ? (
        <div className="space-y-8">
          <VideoUpload 
            onUpload={handleUpload} 
            isLoading={processingStatus.uploading || processingStatus.processing}
          />

          {(processingStatus.uploading || processingStatus.processing) && (
            <ProcessingStatus status={processingStatus} />
          )}

          {uploadHistory.length > 0 && (
            <UploadHistory 
              history={uploadHistory}
              onSelect={(item) => {
                setVideoId(item.id);
                setMetadata(item.metadata);
                setEnhancedVideoUrl(item.videoUrl);
                setProcessingStatus(prev => ({
                  ...prev,
                  progress: 100,
                  enhancement: true,
                  metadata: true,
                }));
              }}
            />
          )}
        </div>
      ) : (
        <>
          <div className="max-w-4xl mx-auto px-4 mb-8">
            <button
              onClick={() => {
                setMetadata(null);
                setEnhancedVideoUrl(null);
                setVideoId(null);
                setError(null);
                setProcessingStatus({
                  uploading: false,
                  processing: false,
                  enhancement: false,
                  metadata: false,
                  progress: 0,
                });
              }}
              className="text-indigo-400 hover:text-indigo-300 text-sm font-semibold transition"
            >
              ← Process Another Video
            </button>
          </div>
          <ResultDisplay metadata={metadata} videoUrl={enhancedVideoUrl} />
        </>
      )}
    </div>
  </div>
);

};

export default App;
