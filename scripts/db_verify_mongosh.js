// Usage: mongosh "mongodb+srv://cspower:<pw>@myatlasclusteredu.9pejmn7.mongodb.net/btm_workout_db" db_verify_mongosh.js
// Or open mongosh and paste the commands below.

// Replica set status
try {
  print('rs.status():');
  printjson(rs.status());
} catch (e) {
  print('rs.status() failed:', e);
}

// Current DB name
print('\nDB name: ' + db.getName());

// Indexes on exercises
print('\nIndexes on exercises:');
printjson(db.exercises.getIndexes());

// Count and sample
print('\nCount: ' + db.exercises.countDocuments({}));
print('Sample doc:');
printjson(db.exercises.findOne({}, {_id:1, name:1, exercise_name:1, body_part:1, equipment:1}));

// Lookup specific ID (replace with the API-inserted id if needed)
// printjson(db.exercises.findOne({_id: ObjectId('68e01bfcdff0ba9a85bad8e6')}));
