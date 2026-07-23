import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Login from "./pages/Login";
import PriceAnalysis from "./pages/PriceAnalysis";
import ProfitAnalysis from "./pages/ProfitAnalysis";
import RiskAnalysis from "./pages/RiskAnalysis";
import Recommendations from "./pages/Recommendations";
import Profile from "./pages/Profile";
import Farms from "./pages/Farms";
import "./App.css";
import RiskLog from "./pages/RiskLog";

function Layout({ children }) {
  return (
    <>
      <Navbar />
      {children}
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <Layout>
              <Home />
            </Layout>
          }
        />
        <Route
          path="/fiyat-tahmini"
          element={
            <Layout>
              <PriceAnalysis />
            </Layout>
          }
        />
        <Route
          path="/kar-hesabi"
          element={
            <Layout>
              <ProfitAnalysis />
            </Layout>
          }
        />
        <Route
          path="/risk-analizi"
          element={
            <Layout>
              <RiskAnalysis />
            </Layout>
          }
        />
        <Route
          path="/oneriler"
          element={
            <Layout>
              <Recommendations />
            </Layout>
          }
        />
        <Route
          path="/bilgilerim"
          element={
            <Layout>
              <Profile />
            </Layout>
          }
        />
        <Route
          path="/tarlalarim"
          element={
            <Layout>
              <Farms />
            </Layout>
          }
        />
        <Route
        path="/Risk-gecmisim"
        element={
            <Layout>
                <RiskLog />
             </Layout>
            }
         />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
