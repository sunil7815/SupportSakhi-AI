import api from "../api/axios";

export async function createKnowledgeItem(payload) {
  const response = await api.post("/knowledge/", payload);
  return response.data;
}

export async function searchKnowledge({
  q,
  category = "",
  limit = 10,
  minScore = 0.15,
}) {
  const params = {
    q,
    limit,
    min_score: minScore,
  };

  if (category) {
    params.category = category;
  }

  const response = await api.get("/knowledge/search", { params });
  return response.data;
}

export async function getKnowledgeItems({
  includeInactive = true,
  category = "",
} = {}) {
  const params = {
    include_inactive: includeInactive,
  };

  if (category) {
    params.category = category;
  }

  const response = await api.get("/knowledge/", { params });
  return response.data;
}

export async function approveKnowledgeItem(knowledgeItemId) {
  const response = await api.put(
    `/knowledge/${knowledgeItemId}/approve`
  );

  return response.data;
}

export async function deactivateKnowledgeItem(knowledgeItemId) {
  const response = await api.put(
    `/knowledge/${knowledgeItemId}/deactivate`
  );

  return response.data;
}