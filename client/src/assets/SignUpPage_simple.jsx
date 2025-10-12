import React from 'react';

function SignUpPage() {
  console.log('SignUpPage component rendering...');
  
  // Simplified version for debugging
  return (
    <div className="auth-page" style={{
      backgroundColor: 'red', 
      minHeight: '100vh',
      padding: '20px',
      color: 'white',
      fontSize: '24px'
    }}>
      <h1>SIGNUP PAGE - COMPONENT RENDERED SUCCESSFULLY</h1>
      <p>If you can see this, the component is working!</p>
      <p>The auth-page div class exists and is rendering.</p>
    </div>
  );
}

export default SignUpPage;