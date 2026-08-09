import api from "../api/axios";

export const getAdminDashboard = async () => {
  const response = await api.get("/dashboard/admin");
  return response.data;
};

export const getAllTickets = async (params = {}) => {
  const response = await api.get("/tickets/", {
    params,
  });

  return response.data;
};

export const getAllUsers = async () => {
  const response = await api.get("/users/");
  return response.data;
};

export const assignTicket = async (
  ticketId,
  userId
) => {
  const response = await api.put(
    "/tickets/" +
      ticketId +
      "/assign/" +
      userId
  );

  return response.data;
};

export const adminUpdateTicket = async (
  ticketId,
  data
) => {
  const response = await api.put(
    "/tickets/" + ticketId,
    data
  );

  return response.data;
};
