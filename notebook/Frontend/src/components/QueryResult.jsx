import React from 'react';

const QueryResult = ({ data }) => {
    return (
        <div>
            <p>{data.answer}</p>
            <h4>Sources:</h4>
            <ul>
                {data.sources.map((doc, index) => (
                    <li key={index}>{doc.metadata.source}</li>
                ))}
            </ul>
        </div>
    );
};

export default QueryResult; 