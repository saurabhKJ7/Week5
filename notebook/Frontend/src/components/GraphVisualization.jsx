import React from 'react';
import Graph from 'react-graph-vis';

const GraphVisualization = ({ graphData }) => {
    const options = {
        layout: {
            hierarchical: false
        },
        edges: {
            color: "#000000"
        },
        height: "500px"
    };

    return (
        <Graph
            graph={graphData}
            options={options}
        />
    );
};

export default GraphVisualization; 