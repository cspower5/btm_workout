import React from 'react';
import AddFormComponent from './AddFormComponent';

function AddBodyPartPage() {
  return (
    <AddFormComponent
      title="Add New Body Part"
      apiEndpoint="/api/v1/add_body_part"
      placeholder="e.g., legs"
    />
  );
}

export default AddBodyPartPage;