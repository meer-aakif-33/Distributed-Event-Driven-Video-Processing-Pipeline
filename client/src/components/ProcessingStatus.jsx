import React, { useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, Zap } from "lucide-react";

const ProcessingStatus = ({ status }) => {
  const [displayProgress, setDisplayProgress] = useState(status.progress);

  useEffect(() => {
    setDisplayProgress(status.progress);
  }, [status.progress]);

  const steps = [
    { name: "Uploading", completed: !status.uploading && status.progress > 30 },
    { name: "Enhancement", completed: status.enhancement },
    { name: "Metadata", completed: status.metadata },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4">
      <div className="bg-white/10 backdrop-blur-2xl rounded-2xl border border-white/20 p-8">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <Zap className="text-yellow-400 animate-pulse" size={24} />
          <h3 className="text-2xl font-bold text-white">Processing Your Video</h3>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <p className="text-gray-300 text-sm">Overall Progress</p>
            <p className="text-white font-bold">{Math.min(displayProgress, 99)}%</p>
          </div>
          <div className="w-full h-3 bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-500 to-blue-600 transition-all duration-300 ease-out"
              style={{ width: `${displayProgress}%` }}
            />
          </div>
        </div>

        {/* Steps */}
        <div className="space-y-3">
          {steps.map((step, idx) => (
            <div key={idx} className="flex items-center gap-3">
              <div className="relative w-6 h-6">
                {step.completed ? (
                  <CheckCircle2 className="text-green-400" size={24} />
                ) : (
                  <div className="w-6 h-6 rounded-full border-2 border-gray-600 flex items-center justify-center">
                    {status.progress > (idx + 1) * 30 && (
                      <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                    )}
                  </div>
                )}
              </div>
              <span className={step.completed ? "text-green-400 font-semibold" : "text-gray-400"}>
                {step.name}
              </span>
            </div>
          ))}
        </div>

        {/* Info Message */}
        <div className="mt-6 p-4 bg-blue-500/20 border border-blue-500/30 rounded-lg">
          <p className="text-blue-300 text-sm">
            ⏱️ This process typically takes 10-30 seconds depending on video size and complexity.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ProcessingStatus;
