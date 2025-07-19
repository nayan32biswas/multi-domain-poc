import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Home from './pages/Home';
import ProjectUpdate from './pages/ProjectUpdate';

import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/projects/:projectId/edit" element={<ProjectUpdate />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
