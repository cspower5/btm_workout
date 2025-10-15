import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './assets/App.jsx';
import './assets/css/index.css';

console.log('main.jsx loaded, about to render App');

document.getElementById('root').textContent = 'Hello from main.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
);

