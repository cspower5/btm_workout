import React from 'react';
import AddFormComponent from './AddFormComponent';

function AddEquipmentPage() {
  return (
    <AddFormComponent
      title="Add New Equipment"
      apiEndpoint="/api/v1/add_equipment"
      placeholder="e.g., dumbbell"
    />
  );
}

export default AddEquipmentPage;
