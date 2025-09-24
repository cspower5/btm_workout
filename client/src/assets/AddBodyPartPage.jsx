import React from 'react';
import AddFormComponent from './AddFormComponent';

function AddBodyPartPage() {
  return (
    <AddFormComponent
      title="Add New Body Part"
      apiEndpoint="/api/add_body_part"
      placeholder="e.g., Forearms"
    />
  );
}

export default AddBodyPartPage;