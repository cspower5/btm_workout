import React from 'react';
// FIX: Switched from BrowserRouter to HashRouter for GitHub Pages compatibility.
import { HashRouter as Router, Routes, Route, Link } from 'react-router-dom'; 
import Home from './Home';
import WorkoutPage from './WorkoutPage';
import NewExerciseForm from './NewExerciseForm';
import SingleExercisePage from './SingleExercisePage';
import AddBodyPartPage from './AddBodyPartPage';
import AddEquipmentPage from './AddEquipmentPage';
import ManageItemsPage from './ManageItemsPage';
import './css/App.css';
import logo from './../assets/images/btm_workout_logo.svg';

function App() {
  return (
    // FIX: Removed the incorrect 'basename="/btm_workout"' prop, as HashRouter 
    // manages the path differently and automatically resolves links correctly.
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>BREAK THE MONOTONY</h1>
          <div className="header-nav">
            <nav>
              <ul>
                <li>
                  <Link to="/">Home</Link>
                </li>
                <li>
                  <Link to="/workout">Generate Workout</Link>
                </li>
                <li>
                  <Link to="/add-exercise">Add Exercise</Link>
                </li>
                <li>
                  <Link to="/add-body-part">Add Body Part</Link>
                </li>
                <li>
                  <Link to="/add-equipment">Add Equipment</Link>
                </li>
                <li>
                  <Link to="/manage-body-parts">Manage Body Parts</Link>
                </li>
                <li>
                  <Link to="/manage-equipment">Manage Equipment</Link>
                </li>
                <li>
                  <Link to="/manage-exercises">Manage Exercises</Link>
                </li>
              </ul>
            </nav>
          </div>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/workout" element={<WorkoutPage />} />
            <Route path="/add-exercise" element={<NewExerciseForm />} />
            <Route path="/add-body-part" element={<AddBodyPartPage />} />
            <Route path="/add-equipment" element={<AddEquipmentPage />} />
            <Route path="/exercise/:name" element={<SingleExercisePage />} />
            <Route path="/manage-body-parts" element={<ManageItemsPage title="Body Parts" fetchUrl="/api/v1/body_parts_list" deleteUrl="/api/v1/delete_body_part" />} />
            <Route path="/manage-equipment" element={<ManageItemsPage title="Equipment" fetchUrl="/api/v1/equipment_list" deleteUrl="/api/v1/delete_equipment" />} />
            <Route path="/manage-exercises" element={<ManageItemsPage title="Exercises" fetchUrl="/api/v1/exercises_list" deleteUrl="/api/v1/delete_exercise" />} />
          </Routes>
        </main>
        <footer className="footer-nav">
          <img src={logo} alt="BREAK THE MONOTONY Logo" className="footer-logo" />
          <nav>
            <ul>
              <li>
                <Link to="/">Home</Link>
              </li>
              <li>
                <Link to="/workout">Generate Workout</Link>
              </li>
              <li>
                <Link to="/add-exercise">Add Exercise</Link>
              </li>
              <li>
                <Link to="/add-body-part">Add Body Part</Link>
              </li>
              <li>
                <Link to="/add-equipment">Add Equipment</Link>
              </li>
              <li>
                <Link to="/manage-body-parts">Manage Body Parts</Link>
              </li>
              <li>
                <Link to="/manage-equipment">Manage Equipment</Link>
              </li>
              <li>
                <Link to="/manage-exercises">Manage Exercises</Link>
              </li>
            </ul>
          </nav>
          <p>© 2024 BTM Workout. All rights reserved.</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
