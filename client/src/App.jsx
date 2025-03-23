import React, { useState, useEffect } from "react";
import axios from "axios";
import VideoUpload from "./components/VideoUpload";
import ResultDisplay from "./components/ResultDisplay";
import './App.css';

const App = () => {
  const [videoId, setVideoId] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [enhancedVideoUrl, setEnhancedVideoUrl] = useState(null);

  useEffect(() => {
    console.log("App mounted.");
  }, []);

  useEffect(() => {
    console.log("State changed:");
    console.log("videoId:", videoId);
    console.log("metadata:", metadata);
    console.log("enhancedVideoUrl:", enhancedVideoUrl);
  }, [videoId, metadata, enhancedVideoUrl]);

  const handleUpload = async (file) => {
    try {
      console.log("Uploading file:", file.name);

      const formData = new FormData();
      formData.append("file", file);

      const res = await axios.post("http://localhost:8000/upload", formData);

      console.log("Upload response:", res.data);

      const { video_id } = res.data;
      setVideoId(video_id);
      connectWebSocket(video_id);
    } catch (error) {
      console.error("Error uploading video:", error);
    }
  };

  const connectWebSocket = (video_id) => {
    console.log("Trying to connect WebSocket for:", video_id);
    const ws = new WebSocket(`ws://localhost:8000/ws?video_id=${video_id}`);

    ws.onopen = () => {
      console.log("WebSocket connected for:", video_id);
    };

    ws.onmessage = (event) => {
      console.log("Raw WebSocket message received:", event.data);

      try {
        const data = JSON.parse(event.data);
        console.log("Parsed WebSocket data:", data);

        if (data.message === "Processing complete!") {
          console.log("Received final processing completion signal.");
          console.log("Metadata:", data.metadata);
          console.log("Enhanced video URL:", data.enhanced_video_url);

          setMetadata(data.metadata);
          setEnhancedVideoUrl(`${data.enhanced_video_url}`);
        } else {
          console.log("WebSocket message (non-final):", data);
        }
      } catch (err) {
        console.error("Failed to parse WebSocket message:", err);
      }
    };

    ws.onerror = (e) => {
      console.error("WebSocket error:", e);
    };

    ws.onclose = () => {
      console.log("WebSocket connection closed.");
    };
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <h1 className="text-3xl font-bold text-center mb-6">Video Processor</h1>
      <VideoUpload onUpload={handleUpload} />
      <ResultDisplay metadata={metadata} videoUrl={enhancedVideoUrl} />
    </div>
  );
};

export default App;
