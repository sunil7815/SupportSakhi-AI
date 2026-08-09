import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import api from "../api/axios";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const getCurrentUser = async () => {
    try {
      const token = localStorage.getItem("access_token");

      if (!token) {
        setUser(null);
        return;
      }

      const response = await api.get("/users/me");
      setUser(response.data);
    } catch (error) {
      console.error("Get current user error:", error);
      localStorage.removeItem("access_token");
      setUser(null);
    }
  };

  const login = async (email, password) => {
    const formData = new URLSearchParams();

    formData.append("username", email);
    formData.append("password", password);

    const response = await api.post(
      "/auth/login",
      formData,
      {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      }
    );

    const token = response.data.access_token;

    localStorage.setItem("access_token", token);

    const userResponse = await api.get("/users/me");

    setUser(userResponse.data);

    return userResponse.data;
  };

  const register = async (name, email, password) => {
    const response = await api.post("/auth/register", {
      name,
      email,
      password,
    });

    return response.data;
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    setUser(null);
  };

  useEffect(() => {
    const loadUser = async () => {
      await getCurrentUser();
      setLoading(false);
    };

    loadUser();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        getCurrentUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
