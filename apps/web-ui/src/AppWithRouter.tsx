import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import App from './App';
import CareerTrackerPage from './components/CareerTrackerPage';

const AppWithRouter: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/career-tracker" element={<CareerTrackerPage />} />
      </Routes>
    </Router>
  );
};

export default AppWithRouter;