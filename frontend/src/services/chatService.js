import api from "../api/axios";


export const sendChatMessage = async ({
  message,
  ticketId = null,
}) => {
  const response = await api.post(
    "/chat/message",
    {
      message,
      ticket_id: ticketId,
    }
  );

  return response.data;
};


export const confirmResolution = async ({
  ticketId,
  resolved,
  attemptedSteps = [],
  failureReason = null,
}) => {
  const response = await api.post(
    `/chat/tickets/${ticketId}/confirm-resolution`,
    {
      resolved,
      attempted_steps: attemptedSteps,
      failure_reason: failureReason,
    }
  );

  return response.data;
};


export const getProofSummary = async (
  ticketId
) => {
  const response = await api.get(
    `/chat/tickets/${ticketId}/proof-summary`
  );

  return response.data;
};


export const getChatContext = async () => {
  const response = await api.get(
    "/chat/context"
  );

  return response.data;
};


export const getChatHealth = async () => {
  const response = await api.get(
    "/chat/health"
  );

  return response.data;
};