import React from 'react';

const DecomposedQueryResult = ({ data }) => {
    return (
        <div>
            <h4>Final Answer:</h4>
            <p>{data.final_answer}</p>
            <h4>Intermediate Steps:</h4>
            <ul>
                {data.intermediate_steps.map((step, index) => (
                    <li key={index}>
                        <strong>Sub-query:</strong> {step[0]}
                        <br />
                        <strong>Answer:</strong> {step[1]}
                    </li>
                ))}
            </ul>
            <h4>Sources:</h4>
            <ul>
                {data.source_documents.map((doc, index) => (
                    <li key={index}>{doc.metadata.source}</li>
                ))}
            </ul>
        </div>
    );
};

export default DecomposedQueryResult; 