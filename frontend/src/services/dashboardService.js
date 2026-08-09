import api from "../api/axios";

export const getMyDashboard = async () => {
  const response = await api.get("/dashboard/my");
  return response.data;
};

export const getAdminDashboard = async () => {
  const response = await api.get("/dashboard/admin");
  return response.data;
};
