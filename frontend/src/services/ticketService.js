import api from "../api/axios";

export const getMyTickets = async (params = {}) => {
  const response = await api.get("/tickets/my", {
    params,
  });

  return response.data;
};

export const getTicketById = async (ticketId) => {
  const response = await api.get("/tickets/" + ticketId);
  return response.data;
};

export const createTicket = async ({
  title,
  description,
  priority,
}) => {
  const response = await api.post(
    "/tickets/",
    null,
    {
      params: {
        title,
        description,
        priority,
      },
    }
  );

  return response.data;
};

export const updateTicket = async (ticketId, data) => {
  const response = await api.put(
    "/tickets/" + ticketId,
    data
  );

  return response.data;
};

export const analyzeTicket = async (ticketId) => {
  const response = await api.post(
    "/ai/tickets/" + ticketId + "/analyze"
  );

  return response.data;
};

export const getTicketComments = async (ticketId) => {
  const response = await api.get(
    "/tickets/" + ticketId + "/comments"
  );

  return response.data;
};

export const addTicketComment = async (ticketId, comment) => {
  const response = await api.post(
    "/tickets/" + ticketId + "/comments",
    {
      comment: comment,
    }
  );

  return response.data;
};
export const getTicketActivity = async (ticketId) => {
  const response = await api.get(
    "/tickets/" + ticketId + "/activity"
  );

  return response.data;
};

