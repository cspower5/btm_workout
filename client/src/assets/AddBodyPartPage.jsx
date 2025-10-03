import React from 'react';
import AddFormComponent from './AddFormComponent';
import { addBodyPart } from '../assets/api/index.jsx';

function AddBodyPartPage() {
  return (
    <AddFormComponent
      title="Add New Body Part"
      apiFunction={addBodyPart}
      placeholder="e.g., legs"
    />
  );
}

export default AddBodyPartPage;