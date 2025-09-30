import React from 'react';
import AddFormComponent from './AddFormComponent';
// FIX: Import the functional API helper (which uses the absolute URL and POST method)
import { addEquipment } from '../assets/api/index.jsx'; 

function AddEquipmentPage() {
  return (
    <AddFormComponent
      title="Add New Equipment"
      // FIX: Pass the dedicated helper function instead of a URL string
      // This ensures the correct absolute URL and POST method are used for submission.
      apiFunction={addEquipment}
      placeholder="e.g., Kettlebell"
    />
  );
}

export default AddEquipmentPage;