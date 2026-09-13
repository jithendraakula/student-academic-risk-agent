import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./routes/ProtectedRoute";
import Login from "./pages/auth/Login";
import MentorDashboard from "./pages/mentor/Dashboard";
import HodDashboard from "./pages/hod/Dashboard";
import DeanDashboard from "./pages/dean/Dashboard";
import AdminDashboard from "./pages/admin/Dashboard";
import StudentProfile from "./pages/mentor/StudentProfile";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route
            path="/mentor"
            element={
              <ProtectedRoute allow={["mentor"]}>
                <MentorDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/mentor/student/:studentId"
            element={
              <ProtectedRoute allow={["mentor", "hod", "dean"]}>
                <StudentProfile />
              </ProtectedRoute>
            }
          />
          <Route
            path="/hod"
            element={
              <ProtectedRoute allow={["hod"]}>
                <HodDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dean"
            element={
              <ProtectedRoute allow={["dean"]}>
                <DeanDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute allow={["admin"]}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
