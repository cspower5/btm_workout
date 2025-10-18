# Field Name Standardization - Implementation Guide

## Summary of Changes

To match Atlas indexes and maintain consistency, we're standardizing all field names to **snake_case**.

### Atlas Indexes (Final State):
```javascript
// exercises
{
  key: { name: 1, body_part: 1, equipment: 1, user_id: 1 },
  name: 'unique_exercises_index'
}

// body_parts  
{
  key: { name: 1, user_id: 1 },
  name: 'unique_body_part_index'  // Note: singular, not plural
}

// equipment
{
  key: { name: 1, user_id: 1 },
  name: 'unique_equipment_index'
}

// users
{
  key: { email: 1 },
  name: 'unique_users_index'
}

// hidden_items
{
  key: { user_id: 1, item_type: 1, item_name: 1 },
  name: 'unique_hidden_item'
}
```

## Field Name Changes

### 1. Exercises Collection
**REMOVE:**
- `exercise_name` field (duplicate of `name`)

**RENAME:**
- `userId` → `user_id`

**KEEP:**
- `name` (lowercased, canonical field)
- `body_part`
- `equipment`
- `target`
- `secondaryMuscles`
- `instructions`
- `description`
- `difficulty`
- `id`

### 2. Body Parts Collection
**RENAME:**
- `userId` → `user_id`

### 3. Equipment Collection
**RENAME:**
- `userId` → `user_id`

### 4. Hidden Items Collection
**RENAME:**
- `userId` → `user_id`
- `itemType` → `item_type`
- `itemName` → `item_name`
- `hiddenAt` → `hidden_at` (if exists)

## Files Updated

### ✅ Completed:
1. `database_setup.py` - Index definitions updated to match Atlas
2. `database_refresh.py` - Exercise mapping and index creation updated
3. `migrations/standardize_field_names.py` - Created migration script

### ⏳ TODO - Application Code:
1. `user_data_manager.py` - Update all field references
2. `flask_server.py` - Update all field references
3. `auth.py` - Check for any userId references

## Migration Steps

### Step 1: Run Migration Script
```bash
cd /home/cspower/Python/projects/btm_workout
python migrations/standardize_field_names.py
```

This will:
- Backup all collections
- Remove `exercise_name` from exercises
- Rename `userId` to `user_id` in all collections
- Rename camelCase fields to snake_case in hidden_items

### Step 2: Update Application Code

Need to update these files to use snake_case:
- `user_data_manager.py`: Replace `userId` with `user_id`
- `flask_server.py`: Replace `userId`, `itemType`, `itemName` with snake_case
- Any references to `exercise_name` should use `name`

### Step 3: Test Locally

1. Run database_setup.py to verify indexes
2. Test all CRUD operations
3. Verify unique constraints work

### Step 4: Deploy

1. Commit all changes
2. Push to GitHub
3. Render will auto-deploy backend

## Search & Replace Guide

### In Python files:
```python
# Find and replace:
"userId"       → "user_id"
"itemType"     → "item_type"
"itemName"     → "item_name"
"hiddenAt"     → "hidden_at"
"exercise_name" → "name"  # In most contexts
.get("exercise_name") → .get("name")
```

### Caution Areas:
- API responses to frontend may still expect camelCase
- Check if frontend uses `exercise_name` anywhere
- Verify all database queries use correct field names

## Verification Commands

```javascript
// Check exercises have correct fields
db.exercises.findOne()

// Verify no exercise_name field exists
db.exercises.countDocuments({"exercise_name": {$exists: true}})  // Should be 0

// Verify user_id exists
db.exercises.countDocuments({"user_id": {$exists: true}})  // Should match total count

// Check indexes match
db.exercises.getIndexes()
db.body_parts.getIndexes()
db.equipment.getIndexes()
db.users.getIndexes()
db.hidden_items.getIndexes()
```

## Rollback Plan

If migration fails, restore from backups:
```javascript
// List backups
db.getCollectionNames().filter(c => c.includes('_backup_'))

// Restore from backup (replace TIMESTAMP with actual timestamp)
db.exercises_backup_TIMESTAMP.find().forEach(doc => {
  db.exercises.insert(doc);
});
```

## Next Actions

1. **Run migration script** to update database
2. **Update Python code** (user_data_manager.py, flask_server.py)
3. **Test locally** with all CRUD operations
4. **Commit and deploy** to production
