import React from "react";
import { Clock, Play } from "lucide-react";

const UploadHistory = ({ history, onSelect }) => {
  if (history.length === 0) {
    return null;
  }

  return (
    <div className="max-w-4xl mx-auto px-4">
      <div className="bg-white/10 backdrop-blur-2xl rounded-2xl border border-white/20 p-8">
        <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
          <Clock size={24} />
          Recent Uploads
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {history.map((item) => (
            <div
              key={item.id}
              className="bg-white/5 hover:bg-white/10 border border-white/10 hover:border-cyan-400/50 rounded-lg p-4 cursor-pointer transition group"
              onClick={() => onSelect(item)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-white font-semibold truncate group-hover:text-cyan-300 transition">
                    {item.filename}
                  </p>
                  <p className="text-gray-400 text-sm mt-1">{item.timestamp}</p>
                </div>
                <Play className="text-cyan-400 flex-shrink-0 ml-2 group-hover:scale-110 transition" size={20} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default UploadHistory;
