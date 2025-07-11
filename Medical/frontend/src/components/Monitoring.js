import React from 'react';

function Monitoring() {
  return (
    <div className="max-w-7xl mx-auto">
      <div className="bg-white shadow sm:rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">System Monitoring</h2>
        
        <div className="aspect-w-16 aspect-h-9">
          <iframe
            src="http://localhost:3001/d/medical-assistant/medical-assistant-metrics?orgId=1&refresh=5s"
            width="100%"
            height="800"
            frameBorder="0"
            title="Grafana Dashboard"
            className="rounded-lg"
          />
        </div>
      </div>
    </div>
  );
}

export default Monitoring; 