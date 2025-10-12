import React from 'react';
import { Link } from 'react-router-dom';

function NavigationTest() {
  return (
    <div style={{ padding: '20px', backgroundColor: 'yellow' }}>
      <h2>Navigation Test</h2>
      <p>This is a test component to verify React Router is working</p>
      <div>
        <Link to="/signup" style={{ marginRight: '10px', padding: '10px', backgroundColor: 'blue', color: 'white' }}>
          Go to Signup
        </Link>
        <Link to="/signin" style={{ padding: '10px', backgroundColor: 'green', color: 'white' }}>
          Go to Signin
        </Link>
      </div>
    </div>
  );
}

export default NavigationTest;