import React from 'react';
import AddFormComponent from './AddFormComponent';

function AddEquipmentPage() {
  return (
    <AddFormComponent
      title="Add New Equipment"
      apiEndpoint="/api/add_equipment"
      placeholder="e.g., Kettlebell"
    />
  );
}

export default AddEquipmentPage;
